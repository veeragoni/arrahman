#!/usr/bin/env python3
"""Discover new A.R. Rahman releases and resolve exact provider links.

Discovery walks the full Spotify artist catalog (albums and singles in every
language), skips releases already curated anywhere in data/source, and appends
the rest to data/source/06-new-releases.json for later curation.

Apple Music links are resolved without an Apple developer account through the
public iTunes Search/Lookup API: the UPC barcode from the Spotify album is
looked up first (exact same release, exact link), falling back to a scored
term search on the iTunes catalog.

Usage:
    python3 scripts/discover_albums.py                       # discover new releases
    python3 scripts/discover_albums.py --max-age-days 120
    python3 scripts/discover_albums.py --backfill-apple --backfill-limit 25
    python3 scripts/discover_albums.py --dry-run

Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build
from build import (
    DEFAULT_PROVIDERS,
    SOURCE_DIR,
    SpotifyAlbumResolver,
    detected_spotify_languages,
    extract_year,
    iter_link_targets,
    load_source_categories,
    normalize_search_text,
    slugify,
    title_token_match_score,
    write_provider_link_to_source,
)

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "discovery-state.json"
ARTWORK_PATH = ROOT / "data" / "artwork.json"
NEW_RELEASES_PATH = SOURCE_DIR / "06-new-releases.json"
SPOTIFY_API = "https://api.spotify.com/v1"
ITUNES_SEARCH_ENDPOINT = "https://itunes.apple.com/search"
ITUNES_LOOKUP_ENDPOINT = "https://itunes.apple.com/lookup"
ITUNES_COUNTRIES = ["IN", "US"]
ITUNES_REQUEST_DELAY = 3.2  # public API allows ~20 requests/minute
# Transient HTTP statuses worth retrying: rate limiting (429) and the
# upstream's own hiccups (5xx). Apple's public API also returns 403 when it
# throttles shared CI IPs, so treat that as transient too.
RETRYABLE_HTTP_STATUSES = frozenset({403, 429, 500, 502, 503, 504})
HTTP_MAX_ATTEMPTS = 4
HTTP_RETRY_BASE_DELAY = 2.0  # seconds; doubled on each successive retry


def urlopen_json_with_retry(request, timeout=15, attempts=HTTP_MAX_ATTEMPTS):
    """Fetch JSON, retrying transient HTTP and network errors with backoff.

    A single 503/429 from Spotify or Apple should not abort the whole weekly
    job, so retryable failures back off exponentially before re-raising.
    """
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            retryable = exc.code in RETRYABLE_HTTP_STATUSES
            if not retryable or attempt == attempts:
                raise
            reason = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == attempts:
                raise
            reason = getattr(exc, "reason", exc)
        delay = HTTP_RETRY_BASE_DELAY * (2 ** (attempt - 1))
        print(
            f"  transient fetch error ({reason}); retry {attempt}/{attempts - 1} "
            f"in {delay:.0f}s",
            file=sys.stderr,
        )
        time.sleep(delay)
    raise RuntimeError("urlopen_json_with_retry exhausted attempts without raising")
YTMUSIC_SEARCH_ENDPOINT = "https://music.youtube.com/youtubei/v1/search?prettyPrint=false"
YTMUSIC_CONTEXT = {"client": {"clientName": "WEB_REMIX", "clientVersion": "1.20250101.00.00", "hl": "en", "gl": "IN"}}
YTMUSIC_REQUEST_DELAY = 1.0
YTMUSIC_MINIMUM_SCORE = 60
ARTIST_NAME = "A.R. Rahman"
APPLE_TERM_SEARCH_MINIMUM_SCORE = 60
# Rahman must be credited on at least this share of tracks for a release to
# count as his own album rather than a multi-composer compilation.
RAHMAN_TRACK_SHARE_MINIMUM = 0.6
ALTERNATE_VERSION_TOKENS = {
    "remix", "remixes", "mix", "lofi", "instrumental", "unplugged", "mashup",
    "reimagined", "imagined", "sped", "slowed", "drill", "dnb", "acoustic",
    "synthwave", "rendition", "reprise", "rework", "redux",
}
# Filler words that distinguish a Spotify album title from a shorter curated
# label without making it a *different* release (e.g. "Tere Ishk Mein (Original
# Motion Picture Soundtrack)" is still the curated "Tere Ishk Mein"). Content
# words NOT in this set (e.g. "dialogues", "score") mark a distinct companion
# release that must not be collapsed into an existing entry.
OST_NOISE_TOKENS = {
    "original", "motion", "picture", "soundtrack", "ost", "ep", "single",
    "from", "the", "deluxe", "edition", "version", "vol", "volume", "feat",
    "featuring", "music", "of",
    # language tags that often appear in Spotify titles
    "tamil", "telugu", "hindi", "kannada", "malayalam", "english", "marathi",
    "bengali", "punjabi", "arabic", "mandarin", "chinese", "persian", "urdu",
}
# Distinct companion albums of an existing film (spoken-word, etc.) that should
# be attached as a new version under the matching film rather than skipped or
# routed to New Releases.
COMPANION_MARKERS = {"dialogues"}


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested in test_discover_albums.py)
# ---------------------------------------------------------------------------

def clean_apple_url(url):
    """Strip tracking params from an iTunes collectionViewUrl."""
    if not isinstance(url, str) or not url:
        return ""
    parsed = urllib.parse.urlsplit(url)
    if not parsed.netloc.endswith("music.apple.com"):
        return ""
    return urllib.parse.urlunsplit(("https", parsed.netloc, parsed.path, "", ""))


def itunes_collections(payload):
    results = payload.get("results", []) if isinstance(payload, dict) else []
    return [
        result
        for result in results
        if isinstance(result, dict)
        and result.get("wrapperType") == "collection"
        and clean_apple_url(result.get("collectionViewUrl", ""))
    ]


def apple_candidate_score(subject, result):
    """Score a fuzzy iTunes term-search result against a subject."""
    url = clean_apple_url(result.get("collectionViewUrl", ""))
    if not url:
        return -1

    haystack = " ".join([
        result.get("collectionName", ""),
        result.get("artistName", ""),
    ])
    normalized_haystack = normalize_search_text(haystack)
    if "rahman" not in normalized_haystack:
        return -1

    expected_language = build.spotify_expected_language(subject)
    detected_languages = detected_spotify_languages(haystack)
    if expected_language and detected_languages and expected_language not in detected_languages:
        return -1

    score = title_token_match_score(subject.get("label", ""), haystack)
    if score < 0:
        return -1

    normalized_label = normalize_search_text(subject.get("label", ""))
    if normalized_label and normalized_label in normalize_search_text(result.get("collectionName", "")):
        score += 40
    if any(term in normalized_haystack for term in ("soundtrack", "motion picture", "original score", "ost")):
        score += 15

    release_year = extract_year(result.get("releaseDate", ""))
    subject_year = subject.get("versionYear") or extract_year(subject.get("date", "")) or subject.get("year")
    if release_year and subject_year:
        delta = abs(int(release_year) - int(subject_year))
        if delta == 0:
            score += 15
        elif delta <= 1:
            score += 8

    if expected_language and expected_language in detected_languages:
        score += 20
    return score


def pick_apple_term_search_link(subject, results, minimum_score=APPLE_TERM_SEARCH_MINIMUM_SCORE):
    best_url = ""
    best_score = -1
    for result in results:
        score = apple_candidate_score(subject, result)
        if score > best_score:
            best_score = score
            best_url = clean_apple_url(result.get("collectionViewUrl", ""))
    return best_url if best_url and best_score >= minimum_score else ""


def ytmusic_albums_from_payload(payload):
    """Pull album results (MPREb… browse ids) out of an InnerTube search
    response, tolerating the deeply nested renderer structure."""
    renderers = []

    def walk(node):
        if isinstance(node, dict):
            renderer = node.get("musicResponsiveListItemRenderer")
            if isinstance(renderer, dict):
                renderers.append(renderer)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    albums = []
    seen = set()
    for renderer in renderers:
        browse_id = ((renderer.get("navigationEndpoint") or {}).get("browseEndpoint") or {}).get("browseId", "")
        if not browse_id.startswith("MPRE") or browse_id in seen:
            continue
        seen.add(browse_id)
        texts = []
        for column in renderer.get("flexColumns", []):
            runs = ((column.get("musicResponsiveListItemFlexColumnRenderer") or {}).get("text") or {}).get("runs", [])
            texts.append("".join(run.get("text", "") for run in runs if isinstance(run, dict)))
        albums.append({
            "browseId": browse_id,
            "title": texts[0] if texts else "",
            "subtitle": " ".join(texts[1:]),
            "url": f"https://music.youtube.com/browse/{browse_id}",
        })
    return albums


def ytmusic_candidate_score(subject, album):
    haystack = " ".join([album.get("title", ""), album.get("subtitle", "")])
    normalized_haystack = normalize_search_text(haystack)
    if "rahman" not in normalized_haystack:
        return -1

    expected_language = build.spotify_expected_language(subject)
    detected_languages = detected_spotify_languages(haystack)
    if expected_language and detected_languages and expected_language not in detected_languages:
        return -1

    score = title_token_match_score(subject.get("label", ""), haystack)
    if score < 0:
        return -1

    normalized_label = normalize_search_text(subject.get("label", ""))
    if normalized_label and normalized_label in normalize_search_text(album.get("title", "")):
        score += 40
    if any(term in normalized_haystack for term in ("soundtrack", "motion picture", "original score", "ost")):
        score += 15

    release_year = extract_year(album.get("subtitle", ""))
    subject_year = subject.get("versionYear") or extract_year(subject.get("date", "")) or subject.get("year")
    if release_year and subject_year:
        delta = abs(int(release_year) - int(subject_year))
        if delta == 0:
            score += 15
        elif delta <= 1:
            score += 8

    if expected_language and expected_language in detected_languages:
        score += 20
    return score


def pick_ytmusic_link(subject, albums, minimum_score=YTMUSIC_MINIMUM_SCORE):
    best_url = ""
    best_score = -1
    for album in albums:
        score = ytmusic_candidate_score(subject, album)
        if score > best_score:
            best_score = score
            best_url = album.get("url", "")
    return best_url if best_url and best_score >= minimum_score else ""


def spotify_release_date_parts(album):
    raw = album.get("release_date", "") if isinstance(album, dict) else ""
    precision = album.get("release_date_precision", "") if isinstance(album, dict) else ""
    year = extract_year(raw)
    if precision == "day" and raw:
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return year, ""
        return year, parsed.strftime("%d-%m-%Y")
    return year, ""


def release_note(album):
    """Build a human-readable note: detected language, type, provenance."""
    haystack = " ".join([
        album.get("name", ""),
        " ".join(
            track.get("name", "")
            for track in (album.get("tracks", {}) or {}).get("items", [])
            if isinstance(track, dict)
        ),
    ])
    parts = []
    languages = sorted(detected_spotify_languages(haystack))
    if languages:
        parts.append("/".join(language.title() for language in languages))
    if normalize_search_text(album.get("album_type", "")) == "single":
        parts.append("Single")
    parts.append("Auto-added via weekly Spotify discovery")
    return " · ".join(parts)


def album_track_items(album):
    tracks = (album.get("tracks") or {}) if isinstance(album, dict) else {}
    items = tracks.get("items", []) if isinstance(tracks, dict) else tracks
    return [track for track in items if isinstance(track, dict)]


def rahman_track_share(album):
    tracks = album_track_items(album)
    if not tracks:
        return 0.0
    credited = sum(
        1
        for track in tracks
        if any(
            "rahman" in normalize_search_text(artist.get("name", ""))
            for artist in track.get("artists", [])
            if isinstance(artist, dict)
        )
    )
    return credited / len(tracks)


def is_alternate_version_title(name):
    tokens = set(normalize_search_text(name).split())
    return bool(tokens & ALTERNATE_VERSION_TOKENS)


def is_companion_album(album):
    """A distinct spoken-word/companion album (e.g. "<Film> (Dialogues)") that
    belongs under an existing film rather than as a standalone release."""
    tokens = set(normalize_search_text(album.get("name", "")).split())
    return bool(tokens & COMPANION_MARKERS)


def companion_version_title(name):
    """Clean a Spotify companion-album title into a film version title:
    "Peddi (Dialogues) [TELUGU]" -> "Peddi (Dialogues)"."""
    cleaned = re.sub(r"\s*\[[^\]]*\]", "", name)  # drop "[TELUGU]" language tags
    # Trim trailing OST descriptors that aren't the companion marker itself.
    cleaned = re.sub(
        r"\s*\((?:original )?(?:motion picture )?soundtrack[^)]*\)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def classify_album(album, min_track_share=RAHMAN_TRACK_SHARE_MINIMUM):
    """Return (accepted, reason). Rejects multi-composer compilations where
    Rahman is only a minority contributor."""
    share = rahman_track_share(album)
    tracks = len(album_track_items(album))
    if share < min_track_share:
        credited = round(share * tracks)
        return False, f"Rahman credited on only {credited}/{tracks} tracks"
    return True, ""


FROM_HINT_PATTERN = re.compile(r'[(\[]\s*from\s+["“]?([^"”)\]]+)', re.IGNORECASE)


def normalized_track_keys(album):
    """Track-name keys with '(From "X")' decorations stripped, so a single's
    'Sukoon (From "Tere Ishk Mein")' matches the album track 'Sukoon'.
    Version markers (Lofi, Reprise, ...) are part of the name and survive,
    so genuinely different versions never match."""
    keys = set()
    for track in album_track_items(album):
        name = FROM_HINT_PATTERN.sub(" ", track.get("name", ""))
        name = re.sub(r"[()\[\]]", " ", name)
        key = slugify(name)
        if key:
            keys.add(key)
    return keys


def is_single(album):
    return normalize_search_text(album.get("album_type", "")) == "single"


def single_subsumed_by_album(single, album):
    """True when every track of the single already appears on the album."""
    if not is_single(single) or is_single(album):
        return False
    if single.get("id") and single.get("id") == album.get("id"):
        return False
    single_keys = normalized_track_keys(single)
    return bool(single_keys) and single_keys <= normalized_track_keys(album)


def from_hint_slugs(album):
    """Album/film titles referenced via '(From "X")' in the release or track names."""
    texts = [album.get("name", "")] + [track.get("name", "") for track in album_track_items(album)]
    slugs = set()
    for text in texts:
        for match in FROM_HINT_PATTERN.finditer(text or ""):
            slug = slugify(match.group(1))
            if slug:
                slugs.add(slug)
    return slugs


def curated_album_ids_by_slug(categories):
    """Map slug(label) -> spotify album id for every curated entry."""
    mapping = {}
    for subject, target in iter_link_targets(categories):
        if subject.get("categoryId") == "new-releases":
            continue
        album_id = spotify_album_id_from_url((target.get("links") or {}).get("spotify", ""))
        slug = slugify(subject.get("label", ""))
        if album_id and slug:
            mapping.setdefault(slug, album_id)
    return mapping


class SubsumptionChecker:
    """Decides whether a discovered single is fully contained in an album —
    either one from the same discovery batch or a curated album referenced
    by the single's '(From "X")' hint."""

    def __init__(self, spotify, curated_ids_by_slug):
        self.spotify = spotify
        self.curated_ids_by_slug = curated_ids_by_slug
        self._album_cache = {}

    def _curated_albums_for(self, single):
        albums = []
        for slug in from_hint_slugs(single):
            album_id = self.curated_ids_by_slug.get(slug)
            if not album_id:
                continue
            if album_id not in self._album_cache:
                try:
                    fetched = self.spotify.full_albums([album_id])
                except Exception as exc:
                    print(f"      WARNING: could not fetch curated album {album_id}: {exc}", file=sys.stderr)
                    fetched = []
                self._album_cache[album_id] = fetched[0] if fetched else None
            if self._album_cache[album_id]:
                albums.append(self._album_cache[album_id])
        return albums

    def container_for(self, single, batch_albums):
        if not is_single(single):
            return None
        for album in list(batch_albums) + self._curated_albums_for(single):
            if single_subsumed_by_album(single, album):
                return album
        return None


# Same confidence floor build.py uses for accepting Spotify album matches.
PROMOTION_MINIMUM_SCORE = 80


def find_curated_match(album, link_targets):
    """Best curated entry for a discovered album, scored like build.py's
    Spotify album resolver (title tokens, language, soundtrack markers)."""
    best = None
    best_score = -1
    for subject, target in link_targets:
        if subject.get("categoryId") == "new-releases":
            continue
        if "spotify" not in subject.get("providers", []):
            continue
        score = build.spotify_album_score(subject, album)
        if score > best_score:
            best = (subject, target)
            best_score = score
    return best if best_score >= PROMOTION_MINIMUM_SCORE else None


def locate_source_target(source_dir, subject):
    """Find the raw source-file dict a subject points at. Returns
    (path, category, target) or (None, None, None)."""
    path, category = build.find_source_category(source_dir, subject.get("categoryId", ""))
    if not path or not category:
        return None, None, None
    subsection = next(
        (c for c in category.get("subsections", []) if c.get("id") == subject.get("subsectionId")),
        None,
    )
    if not subsection:
        return None, None, None
    item_index = int(subject.get("entryIndex") or 0) - 1
    items = subsection.get("items", [])
    if not (0 <= item_index < len(items)):
        return None, None, None
    item = items[item_index]
    if subject.get("type") == "filmVersion":
        version_index = int(subject.get("versionIndex") or 0) - 1
        versions = item.get("versions", [])
        if not (0 <= version_index < len(versions)):
            return None, None, None
        target = versions[version_index]
    else:
        target = item
    if not build.source_target_matches(target, subject):
        return None, None, None
    return path, category, target


def write_provider_link_replacing(source_dir, subject, provider, url):
    """Like build.write_provider_link_to_source, but may replace an existing
    link (used when a full album supersedes a pre-release single link)."""
    path, category, target = locate_source_target(source_dir, subject)
    if not path or not target:
        return False
    if target.get("links", {}).get(provider) == url:
        return False
    target.setdefault("links", {})[provider] = url
    path.write_text(json.dumps(category, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def write_release_date_to_source(source_dir, subject, release_date):
    """Fill in a missing release date so date-based sorting works."""
    path, category, target = locate_source_target(source_dir, subject)
    if not path or not target or not release_date or target.get("date"):
        return False
    target["date"] = release_date
    path.write_text(json.dumps(category, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def promote_album_to_curated(spotify, album, links, link_targets, dry_run=False):
    """Point a matching curated entry (e.g. a film awaiting its soundtrack) at
    a newly released full album. A curated link to a pre-release single is
    replaced only when every song of that single is on the album; an existing
    album link is never touched. Returns (promoted, subject, reason)."""
    if is_single(album) or is_alternate_version_title(album.get("name", "")):
        return False, None, ""
    match = find_curated_match(album, link_targets)
    if not match:
        return False, None, ""
    subject, target = match
    album_url = (links or {}).get("spotify", "")
    if not album_url:
        return False, None, ""

    current = ((target.get("links") or {}).get("spotify", "")).split("?")[0]
    if current and current != album_url:
        current_id = spotify_album_id_from_url(current)
        if not current_id:
            return False, subject, "curated entry has a non-album Spotify link"
        try:
            fetched = spotify.full_albums([current_id])
        except Exception as exc:
            return False, subject, f"could not inspect curated link: {exc}"
        current_album = fetched[0] if fetched else None
        if not current_album:
            return False, subject, "could not inspect curated link"
        if not is_single(current_album):
            return False, subject, "curated entry already links a full album"
        if not single_subsumed_by_album(current_album, album):
            return False, subject, (
                f"curated single {current_album.get('name', '')!r} has songs not on the album"
            )

    if not dry_run:
        for provider in ("spotify", "appleMusic"):
            url = (links or {}).get(provider, "")
            if url and provider in subject.get("providers", []):
                write_provider_link_replacing(SOURCE_DIR, subject, provider, url)
        target.setdefault("links", {})["spotify"] = album_url
        # Fill in the album release date when the curated entry lacks one so
        # the newest-first ordering reflects the actual release day.
        _, release_date = spotify_release_date_parts(album)
        if release_date and not target.get("date"):
            write_release_date_to_source(SOURCE_DIR, subject, release_date)
            target["date"] = release_date
    return True, subject, ""


def attach_companion_to_film(album, links, link_targets, dry_run=False):
    """Attach a companion album (e.g. a Dialogues release) as a new version
    under the matching film entry. Returns (attached, subject, reason)."""
    match = find_curated_match(album, link_targets)
    if not match:
        return False, None, "no matching film"
    subject, _ = match

    path, category = build.find_source_category(SOURCE_DIR, subject.get("categoryId", ""))
    if not path or not category:
        return False, subject, "source category not found"
    subsection = next(
        (s for s in category.get("subsections", []) if s.get("id") == subject.get("subsectionId")),
        None,
    )
    if not subsection:
        return False, subject, "source subsection not found"
    item_index = int(subject.get("entryIndex") or 0) - 1
    items = subsection.get("items", [])
    if not (0 <= item_index < len(items)):
        return False, subject, "film item out of range"
    film = items[item_index]
    versions = film.get("versions")
    if not isinstance(versions, list):
        return False, subject, "matched entry has no versions array"

    language = subject.get("language", "") or ""
    title = companion_version_title(album.get("name", ""))
    spotify_url = (links or {}).get("spotify", "")
    for version in versions:
        same_link = spotify_url and (version.get("links") or {}).get("spotify", "").split("?")[0] == spotify_url
        same_titled = version.get("title") == title and version.get("language") == language
        if same_link or same_titled:
            return False, subject, "companion version already attached"

    _, release_date = spotify_release_date_parts(album)
    new_links = {k: v for k, v in (links or {}).items() if v}
    new_version = {"language": language, "title": title}
    if release_date:
        new_version["date"] = release_date
    if new_links:
        new_version["links"] = new_links

    if not dry_run:
        versions.append(new_version)
        path.write_text(json.dumps(category, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True, subject, ""


def existing_release_index(categories):
    """Collect spotify URLs and (slug, year) labels already curated."""
    spotify_urls = set()
    labels = []
    for subject, target in iter_link_targets(categories):
        url = (target.get("links") or {}).get("spotify", "")
        if url:
            spotify_urls.add(url.split("?")[0])
        label = subject.get("label", "")
        if label:
            labels.append((label, subject.get("versionYear") or subject.get("year")))
    return spotify_urls, labels


def is_existing_release(album, spotify_urls, labels):
    url = build.spotify_album_url(album).split("?")[0]
    if url and url in spotify_urls:
        return True
    name = album.get("name", "")
    album_year = extract_year(album.get("release_date", ""))
    album_slug = slugify(name)
    # Content words in the album title beyond the curated label and benign OST
    # filler — if any remain (e.g. "dialogues", "score"), this is a distinct
    # companion release, not the curated entry.
    name_tokens = set(normalize_search_text(name).split())
    for label, label_year in labels:
        if album_year and label_year and abs(int(album_year) - int(label_year)) > 1:
            continue
        if slugify(label) == album_slug:
            return True
        # Curated titles are usually shorter ("Tere Ishk Mein") than Spotify
        # album names ("Tere Ishk Mein (Original Motion Picture Soundtrack)").
        # Only collapse when the album adds no new content words.
        if title_token_match_score(label, name) >= 0 and album_year and label_year:
            extra = name_tokens - set(build.title_tokens(label)) - OST_NOISE_TOKENS
            if not extra:
                return True
    return False


def build_release_entry(album, apple_url=""):
    year, release_date = spotify_release_date_parts(album)
    links = {}
    spotify_url = build.spotify_album_url(album).split("?")[0]
    if spotify_url:
        links["spotify"] = spotify_url
    if apple_url:
        links["appleMusic"] = apple_url
    entry = {
        "type": "work",
        "title": album.get("name", ""),
        "note": release_note(album),
        "links": links,
        "sources": [spotify_url] if spotify_url else [],
    }
    if year:
        entry["year"] = year
    if release_date:
        entry["date"] = release_date
    return entry


def entry_sort_key(entry):
    year = entry.get("year") or 0
    date_value = entry.get("date", "")
    try:
        parsed = datetime.strptime(date_value, "%d-%m-%Y").date()
    except ValueError:
        parsed = date(int(year) if year else 1900, 1, 1)
    return (parsed, slugify(entry.get("title", "")))


# ---------------------------------------------------------------------------
# State + new-releases source file
# ---------------------------------------------------------------------------

def load_state(path=STATE_PATH):
    if not path.exists():
        return {"schemaVersion": 1, "artistId": "", "seenSpotifyAlbumIds": []}
    state = json.loads(path.read_text(encoding="utf-8"))
    state.setdefault("schemaVersion", 1)
    state.setdefault("artistId", "")
    state.setdefault("seenSpotifyAlbumIds", [])
    return state


def save_state(state, path=STATE_PATH):
    state["seenSpotifyAlbumIds"] = sorted(set(state.get("seenSpotifyAlbumIds", [])))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


MAIN_SUBSECTION_ID = "auto-discovered"
VERSIONS_SUBSECTION_ID = "auto-versions"
SUBSECTION_TEMPLATES = [
    {
        "id": MAIN_SUBSECTION_ID,
        "num": "10.1",
        "title": "Albums & Singles",
        "type": "list",
        "items": [],
    },
    {
        "id": VERSIONS_SUBSECTION_ID,
        "num": "10.2",
        "title": "Remixes, Instrumentals & Alternate Versions",
        "type": "list",
        "items": [],
    },
]


def load_new_releases_category(path=NEW_RELEASES_PATH):
    if path.exists():
        category = json.loads(path.read_text(encoding="utf-8"))
    else:
        category = {
            "id": "new-releases",
            "num": "10",
            "title": "Latest Releases",
            "blurb": "Recent releases discovered automatically from the Spotify artist catalog, pending curation into the main sections.",
            "providers": DEFAULT_PROVIDERS,
            "subsections": [],
        }
    existing = {subsection.get("id"): subsection for subsection in category["subsections"]}
    for template in SUBSECTION_TEMPLATES:
        subsection = existing.get(template["id"])
        if subsection is None:
            category["subsections"].append(json.loads(json.dumps(template)))
        else:
            # The section is pipeline-owned: keep items, refresh metadata.
            for key in ("num", "title", "type"):
                subsection[key] = template[key]
    return category


def subsection_items(category, subsection_id):
    for subsection in category["subsections"]:
        if subsection.get("id") == subsection_id:
            return subsection["items"]
    raise KeyError(subsection_id)


def target_subsection_id(album_name):
    return VERSIONS_SUBSECTION_ID if is_alternate_version_title(album_name) else MAIN_SUBSECTION_ID


def save_new_releases_category(category, path=NEW_RELEASES_PATH):
    for subsection in category["subsections"]:
        subsection["items"].sort(key=entry_sort_key, reverse=True)
    path.write_text(json.dumps(category, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Network clients
# ---------------------------------------------------------------------------

class SpotifyCatalogClient(SpotifyAlbumResolver):
    def _get(self, url):
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token()}",
                "User-Agent": "arrahman-discography-discovery/1.0",
            },
        )
        return urlopen_json_with_retry(request)

    def resolve_artist_id(self):
        params = urllib.parse.urlencode({"q": ARTIST_NAME, "type": "artist", "limit": 10})
        payload = self._get(f"{SPOTIFY_API}/search?{params}")
        wanted = normalize_search_text(ARTIST_NAME)
        candidates = [
            artist
            for artist in payload.get("artists", {}).get("items", [])
            if normalize_search_text(artist.get("name", "")) == wanted
        ]
        if not candidates:
            raise RuntimeError(f"Spotify artist search returned no exact match for {ARTIST_NAME!r}")
        best = max(candidates, key=lambda artist: artist.get("followers", {}).get("total", 0))
        return best["id"]

    def artist_albums(self, artist_id, include_groups="album,single"):
        params = urllib.parse.urlencode({
            "include_groups": include_groups,
            "market": self.market,
            "limit": 50,
        })
        url = f"{SPOTIFY_API}/artists/{artist_id}/albums?{params}"
        albums = []
        while url:
            payload = self._get(url)
            albums.extend(item for item in payload.get("items", []) if isinstance(item, dict))
            url = payload.get("next")
        return albums

    def full_albums(self, album_ids):
        albums = []
        for start in range(0, len(album_ids), 20):
            batch = album_ids[start:start + 20]
            params = urllib.parse.urlencode({"ids": ",".join(batch), "market": self.market})
            payload = self._get(f"{SPOTIFY_API}/albums?{params}")
            albums.extend(album for album in payload.get("albums", []) if isinstance(album, dict))
        return albums


class ItunesClient:
    def __init__(self, delay=ITUNES_REQUEST_DELAY):
        self.delay = delay
        self._last_request = 0.0

    def _get(self, endpoint, params):
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(
            f"{endpoint}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": "arrahman-discography-discovery/1.0"},
        )
        try:
            return urlopen_json_with_retry(request)
        finally:
            self._last_request = time.monotonic()

    def lookup_by_upc(self, upc):
        for country in ITUNES_COUNTRIES:
            payload = self._get(ITUNES_LOOKUP_ENDPOINT, {"upc": upc, "entity": "album", "country": country})
            collections = itunes_collections(payload)
            if collections:
                return clean_apple_url(collections[0].get("collectionViewUrl", ""))
        return ""

    def search_albums(self, term, country="IN"):
        payload = self._get(ITUNES_SEARCH_ENDPOINT, {
            "term": term,
            "entity": "album",
            "country": country,
            "limit": 10,
        })
        return itunes_collections(payload)


class YouTubeMusicClient:
    """Unauthenticated search against YouTube Music's own InnerTube endpoint —
    the same API the web player uses; no API key or account required."""

    def __init__(self, delay=YTMUSIC_REQUEST_DELAY):
        self.delay = delay
        self._last_request = 0.0

    def search_albums(self, query):
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        body = json.dumps({"context": YTMUSIC_CONTEXT, "query": query}).encode("utf-8")
        request = urllib.request.Request(
            YTMUSIC_SEARCH_ENDPOINT,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://music.youtube.com",
                "Referer": "https://music.youtube.com/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        )
        try:
            payload = urlopen_json_with_retry(request)
        finally:
            self._last_request = time.monotonic()
        return ytmusic_albums_from_payload(payload)


def provider_backfill_targets(provider, require_provider=None):
    """Subjects missing a direct link for the provider. Limited to the audited
    subsections (released films and non-film albums/singles) so forthcoming or
    unreleased entries never get speculative links."""
    categories = load_source_categories()
    targets = []
    for subject, target in iter_link_targets(categories):
        links = target.get("links", {})
        if provider not in subject.get("providers", []) or links.get(provider):
            continue
        if require_provider and not links.get(require_provider):
            continue
        if not build.should_audit_missing_direct_links(subject):
            continue
        targets.append((subject, target))
    return targets


def subject_context_suffix(subject):
    context = ", ".join(
        str(part)
        for part in (subject.get("language"), subject.get("versionYear") or subject.get("year"))
        if part
    )
    return f" ({context})" if context else ""


def backfill_spotify_links(spotify, limit, dry_run=False):
    """Retry Spotify album search for every entry still missing a direct link."""
    targets = provider_backfill_targets("spotify")
    total = len(targets)
    # Rotate which entries we attempt each run so the same unresolved titles at
    # the top of the catalog don't monopolise every run's limited budget.
    random.shuffle(targets)
    if limit:
        targets = targets[:limit]
    print(f"Spotify backfill: checking {len(targets)} of {total} entries missing Spotify links.", file=sys.stderr)

    resolved = 0
    failures = 0
    for index, (subject, target) in enumerate(targets, start=1):
        print(f"  [{index}/{len(targets)}] {subject['label']}{subject_context_suffix(subject)}", file=sys.stderr)
        try:
            result = spotify.resolve_album(subject)
        except Exception as exc:
            print(f"      WARNING: Spotify search failed: {exc}", file=sys.stderr)
            failures += 1
            if failures >= 5:
                print("Stopping Spotify backfill after repeated failures.", file=sys.stderr)
                break
            continue
        failures = 0
        if not result.url:
            detail = "no confident match"
            if result.best_name:
                detail += f"; best rejected: {result.best_name} (score {result.best_score})"
            print(f"      {detail}", file=sys.stderr)
            continue
        print(f"      resolved {result.url}", file=sys.stderr)
        if dry_run:
            resolved += 1
            continue
        if write_provider_link_to_source(SOURCE_DIR, subject, "spotify", result.url):
            resolved += 1
        else:
            print("      source JSON not updated; entry already linked or not found", file=sys.stderr)
    print(f"Spotify backfill: resolved {resolved} of {len(targets)} checked entries.", file=sys.stderr)
    return resolved


def ytmusic_query(subject):
    parts = [subject.get("label", "")]
    language = subject.get("language", "")
    if language and language not in {"Other", "Version"}:
        parts.append(language)
    parts.append(ARTIST_NAME)
    return " ".join(part for part in parts if part)


def backfill_ytmusic_links(ytmusic, limit, dry_run=False):
    """Resolve missing YouTube Music album links via InnerTube search."""
    targets = provider_backfill_targets("youtubeMusic")
    total = len(targets)
    random.shuffle(targets)
    if limit:
        targets = targets[:limit]
    print(f"YouTube Music backfill: checking {len(targets)} of {total} entries missing links.", file=sys.stderr)

    resolved = 0
    failures = 0
    for index, (subject, target) in enumerate(targets, start=1):
        print(f"  [{index}/{len(targets)}] {subject['label']}{subject_context_suffix(subject)}", file=sys.stderr)
        try:
            albums = ytmusic.search_albums(ytmusic_query(subject))
        except Exception as exc:
            print(f"      WARNING: YouTube Music search failed: {exc}", file=sys.stderr)
            failures += 1
            if failures >= 5:
                print("Stopping YouTube Music backfill after repeated failures.", file=sys.stderr)
                break
            continue
        failures = 0
        url = pick_ytmusic_link(subject, albums)
        if not url:
            print(f"      no confident match ({len(albums)} candidates)", file=sys.stderr)
            continue
        print(f"      resolved {url}", file=sys.stderr)
        if dry_run:
            resolved += 1
            continue
        if write_provider_link_to_source(SOURCE_DIR, subject, "youtubeMusic", url):
            resolved += 1
        else:
            print("      source JSON not updated; entry already linked or not found", file=sys.stderr)
    print(f"YouTube Music backfill: resolved {resolved} of {len(targets)} checked entries.", file=sys.stderr)
    return resolved


def spotify_album_image(album, preferred=300):
    images = album.get("images") if isinstance(album, dict) else []
    if not isinstance(images, list) or not images:
        return ""
    best = min(
        (image for image in images if isinstance(image, dict) and image.get("url")),
        key=lambda image: abs((image.get("width") or preferred) - preferred),
        default=None,
    )
    return best.get("url", "") if best else ""


def apple_lookup_params(url):
    """(collectionId, storefront) parsed from a music.apple.com album URL."""
    match = re.search(r"music\.apple\.com/(\w\w)/album/[^/]+/(?:id)?(\d+)", url or "")
    if not match:
        return "", ""
    return match.group(2), match.group(1).upper()


def load_artwork_cache(path=ARTWORK_PATH):
    if path.exists():
        cache = json.loads(path.read_text(encoding="utf-8"))
        cache.setdefault("schemaVersion", 1)
        cache.setdefault("byUrl", {})
        return cache
    return {"schemaVersion": 1, "byUrl": {}}


def save_artwork_cache(cache, path=ARTWORK_PATH):
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backfill_artwork(spotify, itunes, dry_run=False):
    """Cache album cover URLs (Spotify first, iTunes for Apple-only links)
    into data/artwork.json, keyed by the entry's provider link."""
    categories = load_source_categories()
    cache = load_artwork_cache()
    by_url = cache["byUrl"]

    spotify_urls_by_id = {}
    apple_urls = []
    for subject, target in iter_link_targets(categories):
        links = target.get("links", {})
        spotify_url = (links.get("spotify") or "").split("?")[0]
        album_id = spotify_album_id_from_url(spotify_url)
        if album_id and spotify_url not in by_url:
            spotify_urls_by_id[album_id] = spotify_url
        elif not album_id and links.get("appleMusic") and links["appleMusic"] not in by_url:
            apple_urls.append(links["appleMusic"])

    print(
        f"Artwork backfill: {len(spotify_urls_by_id)} Spotify albums, "
        f"{len(apple_urls)} Apple-only albums to fetch.",
        file=sys.stderr,
    )
    added = 0
    for album in spotify.full_albums(sorted(spotify_urls_by_id)):
        image = spotify_album_image(album)
        url = spotify_urls_by_id.get(album.get("id", ""))
        if url and image:
            by_url[url] = image
            added += 1

    for apple_url in apple_urls:
        collection_id, storefront = apple_lookup_params(apple_url)
        if not collection_id:
            continue
        try:
            payload = itunes._get(ITUNES_LOOKUP_ENDPOINT, {
                "id": collection_id,
                "entity": "album",
                "country": storefront or "IN",
            })
        except Exception as exc:
            print(f"      WARNING: iTunes artwork lookup failed: {exc}", file=sys.stderr)
            continue
        collections = itunes_collections(payload)
        artwork = collections[0].get("artworkUrl100", "") if collections else ""
        if artwork:
            by_url[apple_url] = artwork.replace("100x100", "300x300")
            added += 1

    if not dry_run and added:
        save_artwork_cache(cache)
    print(f"Artwork backfill: cached {added} new covers ({len(by_url)} total).", file=sys.stderr)
    return added


def backfill_release_dates(spotify, dry_run=False):
    """Fill missing dates from the linked Spotify album's release date so
    newest-first ordering reflects actual release days."""
    categories = load_source_categories()
    targets = []
    for subject, target in iter_link_targets(categories):
        if target.get("date") or subject.get("date"):
            continue
        album_id = spotify_album_id_from_url((target.get("links") or {}).get("spotify", ""))
        if album_id:
            targets.append((subject, album_id))
    print(f"Date backfill: {len(targets)} entries with Spotify links but no release date.", file=sys.stderr)
    if not targets:
        return 0

    dates_by_id = {}
    for album in spotify.full_albums(sorted({album_id for _, album_id in targets})):
        _, release_date = spotify_release_date_parts(album)
        if album.get("id") and release_date:
            dates_by_id[album["id"]] = release_date

    written = 0
    for subject, album_id in targets:
        release_date = dates_by_id.get(album_id, "")
        if not release_date:
            continue
        if dry_run:
            print(f"  would set {subject['label']}{subject_context_suffix(subject)} -> {release_date}", file=sys.stderr)
            written += 1
            continue
        if write_release_date_to_source(SOURCE_DIR, subject, release_date):
            written += 1
    print(f"Date backfill: set {written} release dates.", file=sys.stderr)
    return written


def resolve_apple_link(itunes, subject, upc=""):
    """Exact UPC match first, scored term search second."""
    if upc:
        try:
            url = itunes.lookup_by_upc(upc)
        except (urllib.error.URLError, OSError) as exc:
            print(f"      WARNING: iTunes UPC lookup failed: {exc}", file=sys.stderr)
            url = ""
        if url:
            return url, "upc"
    term = f'{subject.get("label", "")} {ARTIST_NAME}'
    for country in ITUNES_COUNTRIES:
        try:
            results = itunes.search_albums(term, country=country)
        except (urllib.error.URLError, OSError) as exc:
            print(f"      WARNING: iTunes term search failed: {exc}", file=sys.stderr)
            return "", ""
        url = pick_apple_term_search_link(subject, results)
        if url:
            return url, f"search:{country}"
    return "", ""


# ---------------------------------------------------------------------------
# Discovery + backfill
# ---------------------------------------------------------------------------

def album_subject(album):
    """Shape a Spotify album like an iter_link_targets subject for scoring."""
    year = extract_year(album.get("release_date", ""))
    return {
        "categoryId": "new-releases",
        "type": "work",
        "label": album.get("name", ""),
        "language": "",
        "year": year,
        "versionYear": year,
        "date": album.get("release_date", ""),
    }


def discover_new_releases(spotify, itunes, state, max_age_days,
                          min_track_share=RAHMAN_TRACK_SHARE_MINIMUM, dry_run=False):
    artist_id = state.get("artistId") or spotify.resolve_artist_id()
    state["artistId"] = artist_id

    categories = load_source_categories()
    spotify_urls, labels = existing_release_index(categories)
    seen_ids = set(state.get("seenSpotifyAlbumIds", []))
    cutoff = date.today() - timedelta(days=max_age_days)

    recent = []
    for album in spotify.artist_albums(artist_id):
        album_id = album.get("id", "")
        if not album_id or album_id in seen_ids:
            continue
        year, release_date = spotify_release_date_parts(album)
        if release_date:
            released = datetime.strptime(release_date, "%d-%m-%Y").date()
        elif year:
            released = date(int(year), 12, 31)
        else:
            continue
        if released < cutoff:
            continue
        recent.append(album)

    print(f"Discovery: {len(recent)} unseen Spotify releases within {max_age_days} days.", file=sys.stderr)
    if not recent:
        return 0

    accepted = []
    for album in spotify.full_albums([album.get("id") for album in recent]):
        album_id = album.get("id", "")
        name = album.get("name", "")
        if is_existing_release(album, spotify_urls, labels):
            print(f"  skip (already curated): {name}", file=sys.stderr)
            seen_ids.add(album_id)
            continue
        # Companion albums (e.g. spoken Dialogues) often carry no Rahman-credited
        # tracks; they're tied to a real film by the match step below, so they
        # bypass the multi-composer compilation gate.
        if not is_companion_album(album):
            ok, reason = classify_album(album, min_track_share=min_track_share)
            if not ok:
                print(f"  skip ({reason}): {name}", file=sys.stderr)
                seen_ids.add(album_id)
                continue
        accepted.append(album)

    checker = SubsumptionChecker(spotify, curated_album_ids_by_slug(categories))
    batch_albums = [album for album in accepted if not is_single(album)]
    link_targets = list(iter_link_targets(categories))

    category = load_new_releases_category()
    added = 0
    for album in accepted:
        album_id = album.get("id", "")
        name = album.get("name", "")
        container = checker.container_for(album, batch_albums)
        if container:
            print(f"  skip (single contained in album {container.get('name', '')!r}): {name}", file=sys.stderr)
            seen_ids.add(album_id)
            continue
        upc = (album.get("external_ids") or {}).get("upc", "")
        apple_url, method = resolve_apple_link(itunes, album_subject(album), upc=upc)
        entry = build_release_entry(album, apple_url=apple_url)
        if is_companion_album(album):
            attached, subject, reason = attach_companion_to_film(
                album, entry.get("links", {}), link_targets, dry_run=dry_run,
            )
            if attached:
                print(
                    f"  attach (companion version under {subject['label']!r} in "
                    f"{subject['categoryId']}/{subject['subsectionId']}): {name}",
                    file=sys.stderr,
                )
                seen_ids.add(album_id)
                continue
            if reason:
                print(f"      companion attach skipped: {reason}", file=sys.stderr)
            # Fall through: no film matched, treat as an ordinary new release.
        promoted, subject, reason = promote_album_to_curated(
            spotify, album, entry.get("links", {}), link_targets, dry_run=dry_run,
        )
        if promoted:
            print(
                f"  promote (linked curated entry {subject['label']!r} in "
                f"{subject['categoryId']}/{subject['subsectionId']}): {name}",
                file=sys.stderr,
            )
            seen_ids.add(album_id)
            continue
        if reason:
            print(f"      promotion skipped: {reason}", file=sys.stderr)
        bucket = target_subsection_id(name)
        detail = f"apple via {method}" if apple_url else "no Apple match yet"
        print(f"  + [{bucket}] {name} ({entry.get('year', '?')}) [{detail}]", file=sys.stderr)
        subsection_items(category, bucket).append(entry)
        seen_ids.add(album_id)
        added += 1

    state["seenSpotifyAlbumIds"] = sorted(seen_ids)
    if dry_run:
        print(f"Dry run: would add {added} releases.", file=sys.stderr)
        return added
    if added:
        save_new_releases_category(category)
    save_state(state)
    print(f"Discovery: added {added} new releases to {NEW_RELEASES_PATH.name}.", file=sys.stderr)
    return added


FORTHCOMING_SUBSECTION_ID = "forthcoming"


def relocate_released_forthcoming(dry_run=False):
    """Move forthcoming entries whose soundtrack has now released into the
    destination subsection named by their ``releaseTarget`` field. A forthcoming
    item is considered released once it has a past ``date`` and at least one
    direct provider link. Returns the number of entries moved."""
    path, category = build.find_source_category(SOURCE_DIR, "films")
    if not path or not category:
        print("Relocate: films source not found.", file=sys.stderr)
        return 0
    subsections = category.get("subsections", [])
    forthcoming = next((s for s in subsections if s.get("id") == FORTHCOMING_SUBSECTION_ID), None)
    if not forthcoming:
        print("Relocate: no forthcoming subsection.", file=sys.stderr)
        return 0

    today = date.today()
    moved = 0
    remaining = []
    for item in forthcoming.get("items", []):
        target_id = item.get("releaseTarget")
        date_str = item.get("date", "")
        links = item.get("links") or {}
        has_link = bool(links.get("spotify") or links.get("appleMusic"))
        released = False
        if date_str:
            try:
                released = datetime.strptime(date_str, "%d-%m-%Y").date() <= today
            except ValueError:
                released = False
        if not (target_id and released and has_link):
            if target_id and has_link and not released:
                print(
                    f"  forthcoming {item.get('title', '')!r} not yet released ({date_str}); left in place",
                    file=sys.stderr,
                )
            remaining.append(item)
            continue
        destination = next((s for s in subsections if s.get("id") == target_id), None)
        if not destination:
            print(
                f"  WARNING: releaseTarget {target_id!r} for {item.get('title', '')!r} not found; left in place",
                file=sys.stderr,
            )
            remaining.append(item)
            continue
        item.pop("releaseTarget", None)
        if not item.get("year"):
            year = extract_year(date_str)
            if year:
                item["year"] = int(year)
        destination.setdefault("items", []).append(item)
        moved += 1
        print(
            f"  relocate (forthcoming -> {target_id}): {item.get('title', '')}",
            file=sys.stderr,
        )

    if moved:
        forthcoming["items"] = remaining
        if not dry_run:
            path.write_text(json.dumps(category, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Relocate: moved {moved} released forthcoming entr{'y' if moved == 1 else 'ies'}.", file=sys.stderr)
    return moved


def reaudit_new_releases(spotify, min_track_share=RAHMAN_TRACK_SHARE_MINIMUM, dry_run=False):
    """Re-check previously auto-added releases: drop multi-composer
    compilations and singles whose tracks all live on a known album, and move
    remix/instrumental releases into their own subsection."""
    if not NEW_RELEASES_PATH.exists():
        print("Reaudit: no auto-discovered releases file yet.", file=sys.stderr)
        return 0

    category = load_new_releases_category()
    entries = []
    for subsection in category["subsections"]:
        for entry in subsection["items"]:
            entries.append(entry)
        subsection["items"] = []

    albums_by_id = {}
    ids = [spotify_album_id_from_url((entry.get("links") or {}).get("spotify", "")) for entry in entries]
    for album in spotify.full_albums([album_id for album_id in ids if album_id]):
        if album.get("id"):
            albums_by_id[album["id"]] = album

    categories = load_source_categories()
    checker = SubsumptionChecker(spotify, curated_album_ids_by_slug(categories))
    link_targets = list(iter_link_targets(categories))
    batch_albums = [
        album for album in albums_by_id.values()
        if not is_single(album) and classify_album(album, min_track_share=min_track_share)[0]
    ]

    removed = 0
    for entry, album_id in zip(entries, ids):
        album = albums_by_id.get(album_id)
        title = entry.get("title", "")
        if not album:
            print(f"  keep (no Spotify data): {title}", file=sys.stderr)
            subsection_items(category, target_subsection_id(title)).append(entry)
            continue
        ok, reason = classify_album(album, min_track_share=min_track_share)
        if not ok:
            print(f"  remove ({reason}): {title}", file=sys.stderr)
            removed += 1
            continue
        container = checker.container_for(album, batch_albums)
        if container:
            print(f"  remove (single contained in album {container.get('name', '')!r}): {title}", file=sys.stderr)
            removed += 1
            continue
        promoted, subject, reason = promote_album_to_curated(
            spotify, album, entry.get("links", {}), link_targets, dry_run=dry_run,
        )
        if promoted:
            print(
                f"  promote (moved into curated entry {subject['label']!r} in "
                f"{subject['categoryId']}/{subject['subsectionId']}): {title}",
                file=sys.stderr,
            )
            removed += 1
            continue
        if reason:
            print(f"      promotion skipped: {reason}", file=sys.stderr)
        subsection_items(category, target_subsection_id(album.get("name", title))).append(entry)

    if dry_run:
        print(f"Reaudit dry run: would remove {removed} of {len(entries)} entries.", file=sys.stderr)
        return removed
    save_new_releases_category(category)
    print(f"Reaudit: removed {removed} of {len(entries)} auto-added entries.", file=sys.stderr)
    return removed


SPOTIFY_ALBUM_ID_PATTERN = "open.spotify.com/album/"


def spotify_album_id_from_url(url):
    if not isinstance(url, str) or SPOTIFY_ALBUM_ID_PATTERN not in url:
        return ""
    return url.split(SPOTIFY_ALBUM_ID_PATTERN, 1)[1].split("?")[0].split("/")[0]


def backfill_apple_links(spotify, itunes, limit, dry_run=False):
    categories = load_source_categories()
    targets = []
    for subject, target in iter_link_targets(categories):
        links = target.get("links", {})
        if "appleMusic" not in subject.get("providers", []) or links.get("appleMusic"):
            continue
        album_id = spotify_album_id_from_url(links.get("spotify", ""))
        if not album_id:
            continue
        targets.append((subject, album_id))

    total = len(targets)
    random.shuffle(targets)
    if limit:
        targets = targets[:limit]
    print(f"Apple backfill: checking {len(targets)} of {total} entries missing Apple Music links.", file=sys.stderr)

    upc_by_album_id = {}
    if spotify.available:
        for album in spotify.full_albums([album_id for _, album_id in targets]):
            upc = (album.get("external_ids") or {}).get("upc", "")
            if album.get("id") and upc:
                upc_by_album_id[album["id"]] = upc

    resolved = 0
    for index, (subject, album_id) in enumerate(targets, start=1):
        context = ", ".join(
            str(part)
            for part in (subject.get("language"), subject.get("versionYear") or subject.get("year"))
            if part
        )
        suffix = f" ({context})" if context else ""
        print(f"  [{index}/{len(targets)}] {subject['label']}{suffix}", file=sys.stderr)
        url, method = resolve_apple_link(itunes, subject, upc=upc_by_album_id.get(album_id, ""))
        if not url:
            print("      no confident Apple Music match", file=sys.stderr)
            continue
        print(f"      resolved via {method}: {url}", file=sys.stderr)
        if dry_run:
            resolved += 1
            continue
        if write_provider_link_to_source(SOURCE_DIR, subject, "appleMusic", url):
            resolved += 1
        else:
            print("      source JSON not updated; entry already linked or not found", file=sys.stderr)
    print(f"Apple backfill: resolved {resolved} of {len(targets)} checked entries.", file=sys.stderr)
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-age-days", type=int, default=90,
                        help="Only consider Spotify releases newer than this many days")
    parser.add_argument("--skip-discovery", action="store_true",
                        help="Skip new release discovery")
    parser.add_argument("--reaudit", action="store_true",
                        help="Re-check auto-added releases: drop compilations and album-contained singles, re-bucket alternate versions")
    parser.add_argument("--min-track-share", type=float, default=RAHMAN_TRACK_SHARE_MINIMUM,
                        help="Minimum share of tracks crediting Rahman for a release to qualify as his own")
    parser.add_argument("--backfill-apple", action="store_true",
                        help="Also resolve missing appleMusic links on existing entries")
    parser.add_argument("--backfill-spotify", action="store_true",
                        help="Retry Spotify album search for entries still missing a direct link")
    parser.add_argument("--backfill-youtube-music", action="store_true",
                        help="Resolve missing youtubeMusic links via YouTube Music search")
    parser.add_argument("--backfill-dates", action="store_true",
                        help="Fill missing release dates from linked Spotify albums")
    parser.add_argument("--backfill-artwork", action="store_true",
                        help="Cache album cover URLs for linked albums into data/artwork.json")
    parser.add_argument("--backfill-limit", type=int, default=25,
                        help="Maximum existing entries to backfill per run; 0 for no limit")
    parser.add_argument("--relocate-forthcoming", action="store_true",
                        help="Move released forthcoming entries into their releaseTarget subsection")
    parser.add_argument("--itunes-delay", type=float, default=ITUNES_REQUEST_DELAY,
                        help="Seconds between iTunes API requests")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing files")
    args = parser.parse_args()

    spotify = SpotifyCatalogClient()
    if not spotify.available:
        print("ERROR: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are required.", file=sys.stderr)
        return 1

    itunes = ItunesClient(delay=args.itunes_delay)
    if not args.skip_discovery:
        discover_new_releases(spotify, itunes, load_state(), args.max_age_days,
                              min_track_share=args.min_track_share, dry_run=args.dry_run)
    if args.relocate_forthcoming:
        relocate_released_forthcoming(dry_run=args.dry_run)
    if args.reaudit:
        reaudit_new_releases(spotify, min_track_share=args.min_track_share, dry_run=args.dry_run)
    if args.backfill_spotify:
        backfill_spotify_links(spotify, args.backfill_limit, dry_run=args.dry_run)
    if args.backfill_apple:
        backfill_apple_links(spotify, itunes, args.backfill_limit, dry_run=args.dry_run)
    if args.backfill_youtube_music:
        backfill_ytmusic_links(YouTubeMusicClient(), args.backfill_limit, dry_run=args.dry_run)
    if args.backfill_dates:
        backfill_release_dates(spotify, dry_run=args.dry_run)
    if args.backfill_artwork:
        backfill_artwork(spotify, itunes, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
