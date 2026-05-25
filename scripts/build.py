#!/usr/bin/env python3
"""
Build a single-file HTML bundle from the multi-file source.

Usage:
    python3 scripts/build.py            # produces dist/arrahman-discography.html
    python3 scripts/build.py --output custom.html
    python3 scripts/build.py --resolve-links
"""

import sys
import argparse
from html.parser import HTMLParser
import json
import math
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
DATA_JSON = DATA_DIR / "discography.json"
LINK_CACHE = DATA_DIR / "provider-links.json"
APP_JS = ROOT / "app.js"
INDEX_HTML = ROOT / "index.html"
DEFAULT_OUT = ROOT / "dist" / "arrahman-discography.html"
PROVIDERS = ["spotify", "youtubeMusic", "appleMusic", "youtube", "web"]
DEFAULT_PROVIDERS = ["spotify", "youtubeMusic", "appleMusic", "youtube"]
GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
DUCKDUCKGO_HTML_ENDPOINT = "https://duckduckgo.com/html/"
PROVIDER_SEARCH_SITES = {
    "spotify": "open.spotify.com",
    "youtubeMusic": "music.youtube.com",
    "appleMusic": "music.apple.com",
    "youtube": "youtube.com/watch",
}
PROVIDER_URL_PATTERNS = {
    "spotify": re.compile(r"^https://open\.spotify\.com/(album|track|playlist)/"),
    "youtubeMusic": re.compile(r"^https://music\.youtube\.com/(watch|playlist|browse)"),
    "appleMusic": re.compile(r"^https://music\.apple\.com/"),
    "youtube": re.compile(r"^https://(www\.)?(youtube\.com/(watch|playlist)|youtu\.be/)"),
    "web": re.compile(r"^https?://"),
}
FILM_SOUNDTRACK_URL_PATTERNS = {
    "spotify": re.compile(r"^https://open\.spotify\.com/album/"),
    "youtubeMusic": re.compile(r"^https://music\.youtube\.com/(playlist|browse)"),
    "appleMusic": re.compile(r"^https://music\.apple\.com/.*/album/"),
}
COMMON_TITLE_TOKENS = {
    "and", "feat", "film", "from", "movie", "music", "original", "picture",
    "score", "single", "song", "songs", "soundtrack", "the", "version", "with",
    "hindi", "kannada", "malayalam", "marathi", "tamil", "telugu",
}


def compact_empty(value):
    return {key: item for key, item in value.items() if item not in ({}, [], "", None)}


def normalize_links(value):
    if not value:
        return {}
    return {
        provider: url
        for provider, url in value.items()
        if provider in PROVIDERS and isinstance(url, str) and url.strip()
    }


def normalize_search_text(value):
    text = str(value or "")
    text = text.replace("–", " ").replace("—", " ").replace("&", " and ")
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower()
    return " ".join(text.split())


def slugify(value):
    return normalize_search_text(value).replace(" ", "-")


def subject_cache_key(subject):
    return "|".join([
        subject.get("categoryId", ""),
        subject.get("subsectionId", ""),
        subject.get("type", ""),
        slugify(subject.get("label", "")),
        slugify(subject.get("language", "")),
        str(subject.get("year") or ""),
    ])


def provider_url_allowed(provider, url, subject=None):
    subject = subject or {}
    pattern = FILM_SOUNDTRACK_URL_PATTERNS.get(provider) if subject.get("categoryId") == "films" else None
    pattern = pattern or PROVIDER_URL_PATTERNS.get(provider)
    return bool(pattern and isinstance(url, str) and pattern.search(url))


def title_tokens(label):
    return [
        token
        for token in normalize_search_text(label).split()
        if len(token) >= 3 and token not in COMMON_TITLE_TOKENS
    ]


def title_token_match_score(label, haystack):
    tokens = title_tokens(label)
    if not tokens:
        return 0

    haystack_tokens = set(normalize_search_text(haystack).split())
    matched = sum(1 for token in tokens if token in haystack_tokens)
    required = len(tokens) if len(tokens) <= 2 else math.ceil(len(tokens) * 0.6)
    if matched < required:
        return -1
    return matched * 20


def provider_candidate_score(provider, subject, item):
    url = item.get("link", "")
    if not provider_url_allowed(provider, url, subject):
        return -1

    haystack = " ".join([
        item.get("title", ""),
        item.get("snippet", ""),
        url,
    ])
    score = title_token_match_score(subject.get("label", ""), haystack)
    if score < 0:
        return -1

    normalized_haystack = normalize_search_text(haystack)
    normalized_label = normalize_search_text(subject.get("label", ""))
    if normalized_label and normalized_label in normalized_haystack:
        score += 30
    if "rahman" in normalized_haystack:
        score += 25
    if subject.get("year") and str(subject["year"]) in normalized_haystack:
        score += 10
    if provider == "spotify" and "/album/" in url:
        score += 10
    return score


def pick_provider_link(provider, subject, items):
    best_url = None
    best_score = -1
    for item in items:
        score = provider_candidate_score(provider, subject, item)
        if score > best_score:
            best_url = item.get("link")
            best_score = score
    return best_url if best_score >= 0 else None


def normalize_sources(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_providers(value):
    if not value:
        return DEFAULT_PROVIDERS
    return [provider for provider in value if provider in PROVIDERS]


def load_link_cache(path=LINK_CACHE):
    if not path.exists():
        return {"schemaVersion": 1, "links": {}}
    cache = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cache, dict):
        return {"schemaVersion": 1, "links": {}}
    cache.setdefault("schemaVersion", 1)
    cache.setdefault("links", {})
    return cache


def save_link_cache(cache, path=LINK_CACHE):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_link_targets(categories):
    for category in categories:
        for subsection in category.get("subsections", []):
            for index, item in enumerate(subsection.get("items", []), start=1):
                base = {
                    "categoryId": category["id"],
                    "category": category["title"],
                    "subsectionId": subsection["id"],
                    "subsection": subsection["title"],
                    "entryIndex": index,
                }
                if item.get("type") == "film":
                    for version_index, version in enumerate(item.get("versions", []), start=1):
                        yield {
                            **base,
                            "type": "filmVersion",
                            "versionIndex": version_index,
                            "label": version.get("title", ""),
                            "language": version.get("language", ""),
                            "year": item.get("year"),
                            "providers": version.get("providers") or item.get("providers") or subsection.get("providers") or DEFAULT_PROVIDERS,
                        }, version
                else:
                    yield {
                        **base,
                        "type": "work",
                        "label": item.get("title", ""),
                        "language": "",
                        "year": item.get("year"),
                        "providers": item.get("providers") or subsection.get("providers") or DEFAULT_PROVIDERS,
                    }, item


def apply_cached_links(categories, cache):
    cached_links = cache.get("links", {})
    for subject, target in iter_link_targets(categories):
        cached_subject = cached_links.get(subject_cache_key(subject), {})
        for provider, record in cached_subject.get("providers", {}).items():
            url = record.get("url") if isinstance(record, dict) else record
            links = target.get("links", {})
            if provider in subject["providers"] and url and provider_url_allowed(provider, url, subject) and not links.get(provider):
                target.setdefault("links", {})[provider] = url


def provider_search_query(provider, subject):
    if provider == "web":
        parts = [
            '"A R Rahman"',
            f'"{subject["label"]}"',
            "official",
            "article",
        ]
        if subject.get("year"):
            parts.append(str(subject["year"]))
        return " ".join(parts)

    site = PROVIDER_SEARCH_SITES[provider]
    parts = [
        f"site:{site}",
        '"A R Rahman"',
        f'"{subject["label"]}"',
    ]
    language = subject.get("language")
    if language and language not in {"Other", "Version"}:
        parts.append(language)
    if subject.get("categoryId") == "films" and provider in {"spotify", "youtubeMusic", "appleMusic"}:
        parts.extend(['"Original Motion Picture Soundtrack"', "album"])
    if subject.get("year"):
        parts.append(str(subject["year"]))
    return " ".join(parts)


class GoogleCseResolver:
    def __init__(self, api_key=None, cse_id=None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.cse_id = cse_id or os.environ.get("GOOGLE_CSE_ID")
        self.name = "Google Programmable Search"

    @property
    def available(self):
        return bool(self.api_key and self.cse_id)

    def search_items(self, query):
        params = urllib.parse.urlencode({
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": 5,
        })
        request = urllib.request.Request(
            f"{GOOGLE_CSE_ENDPOINT}?{params}",
            headers={"User-Agent": "arrahman-discography-link-resolver/1.0"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("items", [])

    def resolve(self, provider, subject):
        query = provider_search_query(provider, subject)
        items = self.search_items(query)
        return pick_provider_link(provider, subject, items), query


def decode_duckduckgo_url(url):
    if not isinstance(url, str):
        return ""
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    if (not parsed.netloc or parsed.netloc.endswith("duckduckgo.com")) and parsed.path.startswith("/l/"):
        target = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
        return target or url
    return url


class DuckDuckGoResultParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self._current = None
        self._capture_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._current = {
                "link": decode_duckduckgo_url(attrs.get("href", "")),
                "title": "",
                "snippet": "",
            }
            self._capture_title = True

    def handle_data(self, data):
        if self._capture_title and self._current is not None:
            self._current["title"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._capture_title and self._current is not None:
            self._current["title"] = " ".join(self._current["title"].split())
            if self._current["link"] and self._current["title"]:
                self.items.append(self._current)
            self._current = None
            self._capture_title = False


def parse_duckduckgo_results(html):
    parser = DuckDuckGoResultParser()
    parser.feed(html or "")
    return parser.items


class DuckDuckGoResolver:
    name = "DuckDuckGo HTML search"
    available = True

    def search_items(self, query):
        params = urllib.parse.urlencode({"q": query})
        request = urllib.request.Request(
            f"{DUCKDUCKGO_HTML_ENDPOINT}?{params}",
            headers={
                "User-Agent": "Mozilla/5.0 arrahman-discography-link-resolver/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = response.read().decode("utf-8", errors="replace")
        return parse_duckduckgo_results(payload)

    def resolve(self, provider, subject):
        query = provider_search_query(provider, subject)
        items = self.search_items(query)
        return pick_provider_link(provider, subject, items), query


def create_search_resolver(search_engine="auto", google_api_key=None, google_cse_id=None):
    search_engine = (search_engine or "auto").lower()
    google = GoogleCseResolver(api_key=google_api_key, cse_id=google_cse_id)
    if search_engine == "google":
        return google
    if search_engine == "duckduckgo":
        return DuckDuckGoResolver()
    if google.available:
        return google
    return DuckDuckGoResolver()


def cache_provider_link(cache, subject, provider, url, query):
    key = subject_cache_key(subject)
    cached_subject = cache.setdefault("links", {}).setdefault(key, {
        "label": subject.get("label", ""),
        "language": subject.get("language", ""),
        "year": subject.get("year"),
        "providers": {},
    })
    cached_subject.setdefault("providers", {})[provider] = {
        "url": url,
        "query": query,
    }


def search_backend_unavailable_message(resolver, exc):
    if isinstance(exc, urllib.error.HTTPError) and exc.code in {403, 429}:
        return (
            f"Skipping provider link resolution: {resolver.name} returned HTTP {exc.code}. "
            "Build will use cached direct links and generated provider searches."
        )
    return ""


def resolve_missing_links(categories, cache, limit=50, provider_filter=None, search_engine="auto"):
    resolver = create_search_resolver(search_engine=search_engine)
    if not resolver.available:
        print("Skipping provider link resolution: selected search resolver is not available.", file=sys.stderr)
        return 0

    provider_filter = set(provider_filter or PROVIDERS)
    resolved = 0
    checked = 0
    failures = 0
    for subject, target in iter_link_targets(categories):
        links = target.get("links", {})
        for provider in subject["providers"]:
            if provider not in provider_filter or links.get(provider):
                continue
            if limit and checked >= limit:
                return resolved
            checked += 1
            try:
                url, query = resolver.resolve(provider, subject)
            except Exception as exc:
                backend_message = search_backend_unavailable_message(resolver, exc)
                if backend_message:
                    print(backend_message, file=sys.stderr)
                    return resolved
                print(f"WARNING: link resolution failed for {provider} {subject['label']}: {exc}", file=sys.stderr)
                failures += 1
                if failures >= 5:
                    print(f"Stopping provider link resolution after {failures} search failures.", file=sys.stderr)
                    return resolved
                continue
            if not url:
                continue
            failures = 0
            target.setdefault("links", {})[provider] = url
            links = target["links"]
            cache_provider_link(cache, subject, provider, url, query)
            resolved += 1
    return resolved


def normalize_item(item, subsection_type, providers=None):
    if item.get("type") == "film" or subsection_type == "films":
        item_providers = normalize_providers(item.get("providers") or providers)
        versions = []
        for version in item.get("versions", []):
            versions.append(compact_empty({
                "language": version.get("language", ""),
                "title": version.get("title", ""),
                "date": version.get("date", ""),
                "links": normalize_links(version.get("links")),
                "sources": normalize_sources(version.get("sources")),
                "providers": normalize_providers(version.get("providers") or item_providers),
            }))

        return compact_empty({
            "type": "film",
            "year": item.get("year"),
            "note": item.get("note", ""),
            "versions": versions,
        })

    return compact_empty({
        "type": "work",
        "title": item.get("title", ""),
        "year": item.get("year"),
        "date": item.get("date", ""),
        "note": item.get("note", ""),
        "links": normalize_links(item.get("links")),
        "sources": normalize_sources(item.get("sources")),
        "providers": normalize_providers(item.get("providers") or providers),
    })


def load_source_categories():
    if not SOURCE_DIR.exists():
        print(f"ERROR: missing {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    categories = []
    for path in sorted(SOURCE_DIR.glob("*.json")):
        category = json.loads(path.read_text(encoding="utf-8"))
        category_providers = normalize_providers(category.get("providers"))
        normalized = {
            "id": category.get("id", ""),
            "num": category.get("num", ""),
            "title": category.get("title", ""),
            "subsections": [],
        }
        if category.get("blurb"):
            normalized["blurb"] = category["blurb"]
        for subsection in category.get("subsections", []):
            subsection_type = subsection.get("type", "list")
            providers = normalize_providers(subsection.get("providers") or category_providers)
            normalized["subsections"].append({
                "id": subsection.get("id", ""),
                "num": subsection.get("num", ""),
                "title": subsection.get("title", ""),
                "type": subsection_type,
                "providers": providers,
                "items": [
                    normalize_item(item, subsection_type, providers)
                    for item in subsection.get("items", [])
                ],
            })
        categories.append(normalized)

    if not categories:
        print(f"ERROR: no source JSON files found in {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)
    return categories


def quality_subjects(categories):
    for category in categories:
        for subsection in category.get("subsections", []):
            for index, item in enumerate(subsection.get("items", []), start=1):
                base = {
                    "categoryId": category["id"],
                    "category": category["title"],
                    "subsectionId": subsection["id"],
                    "subsection": subsection["title"],
                    "entryIndex": index,
                }
                if item.get("type") == "film":
                    for version_index, version in enumerate(item.get("versions", []), start=1):
                        yield {
                            **base,
                            "type": "filmVersion",
                            "versionIndex": version_index,
                            "label": version.get("title", ""),
                            "language": version.get("language", ""),
                            "year": item.get("year"),
                            "links": version.get("links", {}),
                            "sources": version.get("sources", []),
                            "providers": version.get("providers") or item.get("providers") or subsection.get("providers") or DEFAULT_PROVIDERS,
                        }
                else:
                    yield {
                        **base,
                        "type": "work",
                        "label": item.get("title", ""),
                        "year": item.get("year"),
                        "links": item.get("links", {}),
                        "sources": item.get("sources", []),
                        "providers": item.get("providers") or subsection.get("providers") or DEFAULT_PROVIDERS,
                    }


def build_quality(categories):
    missing_links = []
    missing_sources = []
    for subject in quality_subjects(categories):
        missing = [provider for provider in subject["providers"] if not subject["links"].get(provider)]
        if missing:
            missing_links.append(compact_empty({
                "categoryId": subject["categoryId"],
                "category": subject["category"],
                "subsectionId": subject["subsectionId"],
                "subsection": subject["subsection"],
                "entryIndex": subject["entryIndex"],
                "versionIndex": subject.get("versionIndex"),
                "type": subject["type"],
                "label": subject["label"],
                "language": subject.get("language", ""),
                "year": subject.get("year"),
                "missing": missing,
            }))
        if not subject["sources"]:
            missing_sources.append(compact_empty({
                "categoryId": subject["categoryId"],
                "category": subject["category"],
                "subsectionId": subject["subsectionId"],
                "subsection": subject["subsection"],
                "entryIndex": subject["entryIndex"],
                "versionIndex": subject.get("versionIndex"),
                "type": subject["type"],
                "label": subject["label"],
                "language": subject.get("language", ""),
                "year": subject.get("year"),
            }))

    return {
        "providers": PROVIDERS,
        "missingLinks": missing_links,
        "missingSources": missing_sources,
    }


def build_discography(link_cache_path=LINK_CACHE, resolve_links=False, resolve_limit=50, resolve_providers=None, search_engine="auto"):
    categories = load_source_categories()
    cache = load_link_cache(Path(link_cache_path))
    apply_cached_links(categories, cache)
    if resolve_links:
        resolved = resolve_missing_links(
            categories,
            cache,
            limit=resolve_limit,
            provider_filter=resolve_providers,
            search_engine=search_engine,
        )
        if resolved:
            save_link_cache(cache, Path(link_cache_path))
            print(f"✓ Resolved {resolved} provider links into {link_cache_path}")
    return {
        "schemaVersion": 2,
        "generatedFrom": "data/source/*.json",
        "categories": categories,
        "quality": build_quality(categories),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", default=str(DEFAULT_OUT),
        help="Output path for the bundled HTML"
    )
    parser.add_argument(
        "--link-cache", default=str(LINK_CACHE),
        help="Provider link cache read by every build and updated by --resolve-links"
    )
    parser.add_argument(
        "--resolve-links", action="store_true",
        help="Resolve missing direct provider links using the selected search backend"
    )
    parser.add_argument(
        "--resolve-limit", type=int, default=50,
        help="Maximum missing provider links to query during --resolve-links; use 0 for no limit"
    )
    parser.add_argument(
        "--resolve-provider", choices=PROVIDERS, action="append",
        help="Limit --resolve-links to one provider; can be repeated"
    )
    parser.add_argument(
        "--search-engine", choices=["auto", "google", "duckduckgo"], default="auto",
        help="Search backend for --resolve-links. auto uses Google when GOOGLE_API_KEY and GOOGLE_CSE_ID exist, otherwise DuckDuckGo."
    )
    args = parser.parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Read source files
    html = INDEX_HTML.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")
    data = build_discography(
        link_cache_path=Path(args.link_cache),
        resolve_links=args.resolve_links,
        resolve_limit=args.resolve_limit,
        resolve_providers=args.resolve_provider,
        search_engine=args.search_engine,
    )
    DATA_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    # Build replacement block
    bundled = (
        '<script id="discography-data" type="application/json">\n'
        + data_json
        + "\n</script>\n<script>\n"
        + app_js
        + "\n</script>"
    )

    # Find the script-tag block in index.html and replace it.
    # Use string operations (not regex) so we don't have to worry about backslash escaping.
    start_marker = "<!-- app logic; loads data/discography.json -->"
    end_marker = '<script src="./app.js"></script>'
    start = html.find(start_marker)
    end = html.find(end_marker)
    if start == -1 or end == -1:
        print("ERROR: could not find script-tag block in index.html", file=sys.stderr)
        sys.exit(1)
    end += len(end_marker)

    bundled_html = html[:start] + bundled + html[end:]

    out_path.write_text(bundled_html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"✓ Built {out_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
