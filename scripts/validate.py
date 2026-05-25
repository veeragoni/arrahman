#!/usr/bin/env python3
"""Validate the static site wiring before publishing."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = ROOT / "data" / "discography.json"
SOURCE_DIR = ROOT / "data" / "source"
LINK_CACHE = ROOT / "data" / "provider-links.json"
INDEX_HTML = ROOT / "index.html"
DIST_HTML = ROOT / "dist" / "arrahman-discography.html"
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
PDF_AUDIT = ROOT / "scripts" / "audit_pdf_sources.py"
PROVIDERS = {"spotify", "youtubeMusic", "appleMusic", "youtube", "web"}
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
NONCREATIVE_PROVIDER_EXCEPTIONS = {
    "guest-docs": ["youtube"],
    "guest-films": ["youtube"],
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERROR: {message}")


def count_entries(category: dict) -> int:
    return sum(len(subsection.get("items", [])) for subsection in category.get("subsections", []))


def provider_url_pattern(provider: str, category_id: str = "") -> re.Pattern[str]:
    return FILM_SOUNDTRACK_URL_PATTERNS.get(provider) if category_id == "films" and provider in FILM_SOUNDTRACK_URL_PATTERNS else PROVIDER_URL_PATTERNS[provider]


def expected_noncreative_providers(subsection_id: str) -> list[str]:
    return NONCREATIVE_PROVIDER_EXCEPTIONS.get(subsection_id, ["web", "youtube"])


def validate_links(value: object, path: str, category_id: str = "") -> None:
    require(isinstance(value, dict), f"{path} links must be an object")
    unknown = set(value) - PROVIDERS
    require(not unknown, f"{path} has unknown providers: {', '.join(sorted(unknown))}")
    for provider, url in value.items():
        require(isinstance(url, str), f"{path}.{provider} must be a string")
        pattern = provider_url_pattern(provider, category_id)
        require(pattern.search(url), f"{path}.{provider} must be a direct {provider} URL")


def validate_providers(value: object, path: str) -> list[str] | None:
    if value is None:
        return None
    require(isinstance(value, list), f"{path} providers must be a list")
    require(value, f"{path} providers must not be empty")
    unknown = set(value) - PROVIDERS
    require(not unknown, f"{path} has unknown providers: {', '.join(sorted(unknown))}")
    return value


def validate_link_cache() -> None:
    if not LINK_CACHE.exists():
        return
    cache = json.loads(LINK_CACHE.read_text(encoding="utf-8"))
    require(cache.get("schemaVersion") == 1, "provider-links.json must use schemaVersion 1")
    links = cache.get("links")
    require(isinstance(links, dict), "provider-links.json links must be an object")
    for key, subject in links.items():
        require(isinstance(subject, dict), f"provider-links.json {key} must be an object")
        providers = subject.get("providers")
        require(isinstance(providers, dict), f"provider-links.json {key}.providers must be an object")
        unknown = set(providers) - PROVIDERS
        require(not unknown, f"provider-links.json {key} has unknown providers: {', '.join(sorted(unknown))}")
        for provider, record in providers.items():
            require(isinstance(record, dict), f"provider-links.json {key}.{provider} must be an object")
            url = record.get("url")
            require(isinstance(url, str), f"provider-links.json {key}.{provider}.url must be a string")
            category_id = key.split("|", 1)[0]
            require(provider_url_pattern(provider, category_id).search(url), f"provider-links.json {key}.{provider}.url must be a direct provider URL")


def find_provider_link(categories: list[dict], title: str, provider: str) -> str:
    for category in categories:
        for subsection in category.get("subsections", []):
            for item in subsection.get("items", []):
                if item.get("type") == "film":
                    for version in item.get("versions", []):
                        if version.get("title") == title:
                            return version.get("links", {}).get(provider, "")
                elif item.get("title") == title:
                    return item.get("links", {}).get(provider, "")
    return ""


def validate_source_category(category: dict, source_name: str) -> None:
    required_category_keys = {"id", "num", "title", "subsections"}
    required_subsection_keys = {"id", "num", "title", "type", "items"}
    require(required_category_keys <= category.keys(), f"{source_name}: category is missing keys")
    category_providers = validate_providers(category.get("providers"), f"{source_name}:{category['id']}")
    if category["id"] == "ads":
        require(category_providers == ["youtube"], "Advertisements & Ringtones must use the YouTube provider")
    if category["id"] == "noncreative":
        require(category_providers == ["web", "youtube"], "Other Work, Institutions & Curation must use the Web and YouTube providers")
    require(isinstance(category["subsections"], list), f"{source_name}: subsections must be a list")
    require(count_entries(category) > 0, f"{source_name}: category must contain entries")
    for subsection in category["subsections"]:
        require(required_subsection_keys <= subsection.keys(), f"{source_name}: subsection is missing keys")
        require(subsection["type"] in {"films", "list"}, f"{source_name}: unknown subsection type {subsection['type']}")
        providers = validate_providers(subsection.get("providers"), f"{source_name}:{subsection['id']}")
        effective_providers = providers or category_providers
        if category["id"] == "ads":
            require(effective_providers == ["youtube"], "Advertisements & Ringtones subsections must use the YouTube provider")
        if category["id"] == "noncreative":
            expected_providers = expected_noncreative_providers(subsection["id"])
            require(
                effective_providers == expected_providers,
                f"Other Work, Institutions & Curation subsection {subsection['id']} must use providers {expected_providers}",
            )
        if subsection["id"] == "videos-film":
            require(providers == ["youtube"], "Video of Film Songs must use the YouTube provider")
        require(isinstance(subsection["items"], list), f"{source_name}: {subsection['id']} items must be a list")
        for idx, item in enumerate(subsection["items"], start=1):
            item_path = f"{source_name}:{subsection['id']}[{idx}]"
            require("y" not in item, f"{item_path} must use year, not y")
            require(item.get("type") in {"film", "work"}, f"{item_path} must declare type film or work")
            item_providers = validate_providers(item.get("providers"), f"{item_path}.providers")
            effective_item_providers = item_providers or effective_providers
            if category["id"] == "ads":
                require(effective_item_providers == ["youtube"], "Advertisements & Ringtones entries must use the YouTube provider")
            if category["id"] == "noncreative":
                expected_providers = expected_noncreative_providers(subsection["id"])
                require(
                    effective_item_providers == expected_providers,
                    f"Other Work, Institutions & Curation entries in {subsection['id']} must use providers {expected_providers}",
                )
            if item["type"] == "film":
                require("year" in item, f"{item_path} film must have year")
                require(isinstance(item.get("versions"), list) and item["versions"], f"{item_path} film must have versions")
                require("links" not in item, f"{item_path} film links belong on versions")
                for version_idx, version in enumerate(item["versions"], start=1):
                    version_path = f"{item_path}.versions[{version_idx}]"
                    require(version.get("language"), f"{version_path} must have language")
                    require(version.get("title"), f"{version_path} must have title")
                    version_providers = validate_providers(version.get("providers"), f"{version_path}.providers")
                    if category["id"] == "ads":
                        require((version_providers or effective_item_providers) == ["youtube"], "Advertisements & Ringtones versions must use the YouTube provider")
                    validate_links(version.get("links", {}), version_path, category["id"])
                    require(isinstance(version.get("sources", []), list), f"{version_path}.sources must be a list")
            else:
                require(item.get("title"), f"{item_path} work must have title")
                validate_links(item.get("links", {}), item_path, category["id"])
                require(isinstance(item.get("sources", []), list), f"{item_path}.sources must be a list")


def main() -> None:
    require(SOURCE_DIR.exists(), "missing data/source")
    validate_link_cache()
    source_files = sorted(SOURCE_DIR.glob("*.json"))
    require(source_files, "data/source must contain category JSON files")
    source_ids = set()
    source_total = 0
    for source_file in source_files:
        category = json.loads(source_file.read_text(encoding="utf-8"))
        validate_source_category(category, source_file.name)
        require(category["id"] not in source_ids, f"duplicate source category id {category['id']}")
        source_ids.add(category["id"])
        source_total += count_entries(category)

    require(DATA_JSON.exists(), "missing data/discography.json")
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    categories = data.get("categories")
    require(isinstance(categories, list), "discography.json must contain a categories array")
    require(categories, "categories array must not be empty")

    required_category_keys = {"id", "num", "title", "subsections"}
    required_subsection_keys = {"id", "num", "title", "type", "items"}
    for category in categories:
        require(required_category_keys <= category.keys(), f"category is missing keys: {category!r}")
        require(isinstance(category["subsections"], list), f"{category['id']} subsections must be a list")
        require(count_entries(category) > 0, f"{category['id']} must contain entries")
        for subsection in category["subsections"]:
            require(required_subsection_keys <= subsection.keys(), f"subsection is missing keys: {subsection!r}")
            require(isinstance(subsection["items"], list), f"{subsection['id']} items must be a list")
            if category["id"] == "ads":
                require(subsection.get("providers") == ["youtube"], "generated Advertisements & Ringtones must use YouTube provider")
                for item in subsection["items"]:
                    require(item.get("providers") == ["youtube"], "generated Advertisements & Ringtones entries must use YouTube provider")
            if category["id"] == "noncreative":
                expected_providers = expected_noncreative_providers(subsection["id"])
                require(
                    subsection.get("providers") == expected_providers,
                    f"generated Other Work, Institutions & Curation subsection {subsection['id']} must use providers {expected_providers}",
                )
                for item in subsection["items"]:
                    require(
                        item.get("providers") == expected_providers,
                        f"generated Other Work, Institutions & Curation entries in {subsection['id']} must use providers {expected_providers}",
                    )
            if subsection["id"] == "videos-film":
                require(subsection.get("providers") == ["youtube"], "generated Video of Film Songs must use YouTube provider")
            for item_idx, item in enumerate(subsection["items"], start=1):
                item_path = f"{category['id']}:{subsection['id']}[{item_idx}]"
                if item.get("type") == "film":
                    for version_idx, version in enumerate(item.get("versions", []), start=1):
                        validate_links(version.get("links", {}), f"{item_path}.versions[{version_idx}]", category["id"])
                else:
                    validate_links(item.get("links", {}), item_path, category["id"])

    legacy_data_files = sorted(path.name for path in (ROOT / "data").glob("*.js"))
    require(not legacy_data_files, f"legacy data JS files remain: {', '.join(legacy_data_files)}")

    html = INDEX_HTML.read_text(encoding="utf-8")
    require('<script src="./app.js"></script>' in html, "index.html must load app.js")
    require('src="./data/' not in html, "index.html must not load data as JavaScript")
    require('data-stat-total="true"' in html, "index.html total stat must be data-driven")
    require("data-stat-subsections" in html or "data-stat-categories" in html, "index.html stat cards must declare data scopes")
    require('<nav class="cats" aria-label="Discography sections">' in html, "category nav must expose a sections label")
    require('<nav class="langs" aria-label="Album language filter">' in html, "index.html must include a language filter nav")
    require('</nav>\n  </div>\n\n  <!-- ===== MAIN ===== -->' in html, "category nav must live inside the sticky search bar")
    require("overflow-x: auto" not in html, "category nav must not use horizontal scrolling")
    require(".cats-inner {\n    display: flex;\n    flex-wrap: wrap;" in html, "category nav pills must wrap")
    require(".lang-tamil" in html and ".lang-telugu" in html and ".lang-hindi" in html, "language badges must have per-language colors")
    for element_id in ("result-prev", "result-next", "result-position"):
        require(f'id="{element_id}"' in html, f"index.html must include search result navigation element #{element_id}")

    require(WORKFLOW.exists(), "missing GitHub Pages workflow")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("actions/deploy-pages" in workflow, "workflow must deploy with actions/deploy-pages")
    require("python3 scripts/build.py" in workflow, "workflow must build generated site data")
    require("--resolve-spotify-albums" in workflow, "workflow must resolve missing film Spotify album links")
    require("--resolve-links" not in workflow, "workflow must not perform generic live provider link resolution")
    require("--search-engine" not in workflow, "workflow must not depend on a live search backend")
    require("SPOTIFY_CLIENT_ID" in workflow, "workflow must pass SPOTIFY_CLIENT_ID to the build")
    require("SPOTIFY_CLIENT_SECRET" in workflow, "workflow must pass SPOTIFY_CLIENT_SECRET to the build")
    require("GOOGLE_API_KEY" not in workflow, "workflow must not depend on GOOGLE_API_KEY")
    require("GOOGLE_CSE_ID" not in workflow, "workflow must not depend on GOOGLE_CSE_ID")

    total = sum(count_entries(category) for category in categories)
    require(total == source_total, f"generated total {total} does not match source total {source_total}")
    gandhi_spotify = find_provider_link(categories, "Gandhi Vs Godse – Ek Yudh", "spotify")
    require(not gandhi_spotify or "open.spotify.com/album/" in gandhi_spotify, "Gandhi Vs Godse Spotify link must be an album URL")

    quality = data.get("quality")
    require(isinstance(quality, dict), "discography.json must contain quality metadata")
    missing_links = quality.get("missingLinks")
    missing_sources = quality.get("missingSources")
    require(isinstance(missing_links, list), "quality.missingLinks must be a list")
    require(isinstance(missing_sources, list), "quality.missingSources must be a list")

    app_js = (ROOT / "app.js").read_text(encoding="utf-8")
    for stat_id in ("stat-films", "stat-singles", "stat-ads", "stat-total"):
        require(f"getElementById('{stat_id}')" not in app_js, "app.js must compute hero stats from data-stat attributes")
    require("appleMusic" in app_js, "app.js must support Apple Music links")
    require("web:" in app_js, "app.js must support Web reference links")
    require("const iconSpotify = `<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><circle cx=\"12\" cy=\"12\" r=\"11.4\" fill=\"#1DB954\"" in app_js, "app.js must use a green circular Spotify icon")
    require("const iconYouTubeMusic" in app_js, "app.js must use a distinct YouTube Music icon")
    require("className: 'ytmusic'" in app_js, "YouTube Music links must use the ytmusic class")
    require("const iconAppleMusic" in app_js, "app.js must use a distinct Apple Music icon")
    require("'https://music.apple.com/us/search?term=' + encodeURIComponent('A R Rahman ' + q)" in app_js, "Apple Music fallback must use a storefront-scoped search URL")
    require("'https://music.apple.com/search?term=' + encodeURIComponent('A R Rahman ' + q)" not in app_js, "Apple Music fallback must not use the no-storefront search URL")
    require("'https://www.google.com/search?q=' + encodeURIComponent(q + ' spotify')" not in app_js, "Spotify must not fall back to Google search")
    require("'https://open.spotify.com/search/' + encodeURIComponent('A R Rahman ' + q)" in app_js, "Spotify fallback must use Spotify search")
    require("if (!directUrl && !provider.search) return ''" in app_js, "app.js must hide providers without direct links or generated search fallbacks")
    require("youtube:" in app_js, "app.js must support YouTube links")
    require("function filmProviderQuery" in app_js, "app.js must build film provider searches with language context")
    require("function languageKey" in app_js, "app.js must normalize language filter keys")
    require("data-language" in app_js, "film version rows must expose language data for filtering")
    require("const languageContainer = document.getElementById('languages')" in app_js, "app.js must build the language filter")
    require("renderProviderLinks(filmProviderQuery(title, version.language)" in app_js, "film version provider links must search by title and language")
    require("data-quality" in app_js, "app.js must render a data-quality view")
    require("navigateResults" in app_js, "app.js must support result navigation")
    require("active-result" in app_js, "app.js must mark the active search result")

    require(DIST_HTML.exists(), "missing dist/arrahman-discography.html")
    dist_html = DIST_HTML.read_text(encoding="utf-8")
    require("'https://www.google.com/search?q=' + encodeURIComponent(q + ' spotify')" not in dist_html, "dist HTML must not use Google for Spotify fallback search")
    require("'https://open.spotify.com/search/' + encodeURIComponent('A R Rahman ' + q)" in dist_html, "dist HTML must use Spotify search fallback")
    require("'https://music.apple.com/us/search?term=' + encodeURIComponent('A R Rahman ' + q)" in dist_html, "dist HTML must use a storefront-scoped Apple Music search fallback")
    require("'https://music.apple.com/search?term=' + encodeURIComponent('A R Rahman ' + q)" not in dist_html, "dist HTML must not use the no-storefront Apple Music search fallback")

    audit = subprocess.run([sys.executable, str(PDF_AUDIT)], cwd=ROOT, text=True, capture_output=True)
    require(audit.returncode == 0, (audit.stderr or audit.stdout).strip())

    print(f"OK: {len(categories)} categories, {total} entries")


if __name__ == "__main__":
    main()
