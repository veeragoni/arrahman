#!/usr/bin/env python3
"""Unit tests for build-time provider link enrichment."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
import urllib.error
import unittest

import build


class ProviderLinkResolutionTests(unittest.TestCase):
    def test_default_providers_include_regular_youtube(self) -> None:
        self.assertEqual(
            build.normalize_providers(None),
            ["spotify", "youtubeMusic", "appleMusic", "youtube"],
        )

    def test_youtube_icon_uses_red_brand_fill_by_default(self) -> None:
        app_js = (Path(__file__).resolve().parent.parent / "app.js").read_text(encoding="utf-8")

        icon_match = re.search(r"const iconYouTube = `([^`]+)`;", app_js)

        self.assertIsNotNone(icon_match)
        icon_svg = icon_match.group(1)
        self.assertNotIn('fill="currentColor"', icon_svg)
        self.assertIn('fill="#FF0000"', icon_svg)
        self.assertIn('fill="#FFFFFF"', icon_svg)

    def test_film_soundtrack_spotify_selection_requires_album_url(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "work",
            "label": "Gandhi Vs Godse – Ek Yudh",
            "language": "",
            "year": 2023,
        }
        items = [
            {
                "link": "https://open.spotify.com/album/wrong",
                "title": "Gandhi Talks",
                "snippet": "A.R. Rahman Gandhi Talks soundtrack",
            },
            {
                "link": "https://open.spotify.com/track/0zm66ruXxDQnr70T9JviFz",
                "title": 'Vaishnav Jan To (From "Gandhi Godse Ek Yudh")',
                "snippet": "A.R. Rahman, Shreya Ghoshal",
            },
            {
                "link": "https://open.spotify.com/album/right",
                "title": "Gandhi Godse Ek Yudh Original Motion Picture Soundtrack",
                "snippet": "A.R. Rahman 2023",
            },
        ]

        selected = build.pick_provider_link("spotify", subject, items)

        self.assertEqual(selected, "https://open.spotify.com/album/right")

    def test_film_soundtrack_spotify_selection_rejects_track_when_no_album_matches(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "work",
            "label": "Gandhi Vs Godse – Ek Yudh",
            "language": "",
            "year": 2023,
        }
        items = [
            {
                "link": "https://open.spotify.com/track/0zm66ruXxDQnr70T9JviFz",
                "title": 'Vaishnav Jan To (From "Gandhi Godse Ek Yudh")',
                "snippet": "A.R. Rahman, Shreya Ghoshal",
            }
        ]

        selected = build.pick_provider_link("spotify", subject, items)

        self.assertIsNone(selected)

    def test_film_soundtrack_spotify_selection_rejects_conflicting_language_result(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Roja",
            "language": "Tamil",
            "year": 1992,
        }
        items = [
            {
                "link": "https://open.spotify.com/album/wrong",
                "title": "Roja Marathi Original Motion Picture Soundtrack",
                "snippet": "A.R. Rahman 1992",
            }
        ]

        selected = build.pick_provider_link("spotify", subject, items)

        self.assertIsNone(selected)

    def test_cached_provider_links_are_applied_without_overwriting_source_links(self) -> None:
        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "hindi-undubbed",
                        "title": "Hindi Undubbed Films",
                        "providers": ["spotify", "appleMusic"],
                        "items": [
                            {
                                "type": "work",
                                "title": "Gandhi Vs Godse – Ek Yudh",
                                "year": 2023,
                                "links": {"appleMusic": "https://music.apple.com/existing"},
                                "providers": ["spotify", "appleMusic"],
                            }
                        ],
                    }
                ],
            }
        ]
        cache = {
            "schemaVersion": 1,
            "links": {
                "films|hindi-undubbed|work|gandhi-vs-godse-ek-yudh||2023": {
                    "providers": {
                        "spotify": {"url": "https://open.spotify.com/album/right"},
                        "appleMusic": {"url": "https://music.apple.com/from-cache"},
                    }
                }
            },
        }

        build.apply_cached_links(categories, cache)
        links = categories[0]["subsections"][0]["items"][0]["links"]

        self.assertEqual(links["spotify"], "https://open.spotify.com/album/right")
        self.assertEqual(links["appleMusic"], "https://music.apple.com/existing")

    def test_cached_film_soundtrack_spotify_track_is_rejected(self) -> None:
        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "hindi-undubbed",
                        "title": "Hindi Undubbed Films",
                        "providers": ["spotify"],
                        "items": [
                            {
                                "type": "work",
                                "title": "Gandhi Vs Godse – Ek Yudh",
                                "year": 2023,
                                "providers": ["spotify"],
                            }
                        ],
                    }
                ],
            }
        ]
        cache = {
            "schemaVersion": 1,
            "links": {
                "films|hindi-undubbed|work|gandhi-vs-godse-ek-yudh||2023": {
                    "providers": {
                        "spotify": {"url": "https://open.spotify.com/track/0zm66ruXxDQnr70T9JviFz"},
                    }
                }
            },
        }

        build.apply_cached_links(categories, cache)

        self.assertNotIn("links", categories[0]["subsections"][0]["items"][0])

    def test_film_soundtrack_provider_query_targets_album_pages(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "work",
            "label": "Gandhi Vs Godse – Ek Yudh",
            "language": "",
            "year": 2023,
        }

        query = build.provider_search_query("spotify", subject)

        self.assertIn('"Original Motion Picture Soundtrack"', query)
        self.assertIn("album", query)

    def test_noncreative_provider_query_targets_web_references(self) -> None:
        subject = {
            "categoryId": "noncreative",
            "type": "work",
            "label": "KM Music Conservatory (KMMC)",
            "language": "",
            "year": None,
        }

        query = build.provider_search_query("web", subject)

        self.assertIn('"A R Rahman"', query)
        self.assertIn('"KM Music Conservatory (KMMC)"', query)
        self.assertIn("official", query)
        self.assertNotIn("open.spotify.com", query)

    def test_cached_noncreative_web_link_is_applied(self) -> None:
        categories = [
            {
                "id": "noncreative",
                "title": "Other Work, Institutions & Curation",
                "subsections": [
                    {
                        "id": "initiatives",
                        "title": "Initiatives (Self)",
                        "providers": ["web"],
                        "items": [
                            {
                                "type": "work",
                                "title": "KM Music Conservatory (KMMC)",
                                "providers": ["web"],
                            }
                        ],
                    }
                ],
            }
        ]
        cache = {
            "schemaVersion": 1,
            "links": {
                "noncreative|initiatives|work|km-music-conservatory-kmmc||": {
                    "providers": {
                        "web": {"url": "https://www.kmmc.in/"},
                    }
                }
            },
        }

        build.apply_cached_links(categories, cache)

        links = categories[0]["subsections"][0]["items"][0]["links"]
        self.assertEqual(links["web"], "https://www.kmmc.in/")

    def test_duckduckgo_results_decode_redirect_links(self) -> None:
        html = """
        <html>
          <body>
            <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.kmmc.in%2Fthe-conservatory%2F&amp;rut=abc">
              The Conservatory - kmmc
            </a>
            <a class="result__a" href="https://example.com/plain">
              Plain result
            </a>
            <a class="result__a" href="/l/?uddg=https%3A%2F%2Fwww.kmmc.in%2Fabout-us%2F&amp;rut=def">
              About Us - kmmc
            </a>
          </body>
        </html>
        """

        items = build.parse_duckduckgo_results(html)

        self.assertEqual(items[0]["link"], "https://www.kmmc.in/the-conservatory/")
        self.assertEqual(items[0]["title"], "The Conservatory - kmmc")
        self.assertEqual(items[1]["link"], "https://example.com/plain")
        self.assertEqual(items[2]["link"], "https://www.kmmc.in/about-us/")

    def test_auto_search_resolver_uses_duckduckgo_without_google_keys(self) -> None:
        resolver = build.create_search_resolver(
            search_engine="auto",
            google_api_key="",
            google_cse_id="",
        )

        self.assertIsInstance(resolver, build.DuckDuckGoResolver)

    def test_auto_search_resolver_prefers_google_when_keys_exist(self) -> None:
        resolver = build.create_search_resolver(
            search_engine="auto",
            google_api_key="key",
            google_cse_id="cse",
        )

        self.assertIsInstance(resolver, build.GoogleCseResolver)

    def test_quality_missing_links_only_audits_album_like_music_entries(self) -> None:
        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "films-main",
                        "title": "Films with multi-language releases",
                        "providers": ["spotify", "youtube"],
                        "items": [
                            {
                                "type": "film",
                                "year": 1992,
                                "versions": [
                                    {
                                        "language": "Tamil",
                                        "title": "Roja",
                                        "links": {"spotify": "https://open.spotify.com/album/roja"},
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "id": "forthcoming",
                        "title": "Forthcoming — In Progress",
                        "providers": ["spotify", "youtube"],
                        "items": [
                            {"type": "work", "title": "Future Film", "year": 2027}
                        ],
                    },
                ],
            },
            {
                "id": "nonfilm",
                "title": "Non-Film Compositions",
                "subsections": [
                    {
                        "id": "albums",
                        "title": "Albums / Collaborations",
                        "providers": ["spotify", "youtube"],
                        "items": [
                            {"type": "work", "title": "Vande Mataram", "year": 1997}
                        ],
                    },
                    {
                        "id": "tv-web",
                        "title": "TV / Web Series",
                        "providers": ["spotify", "youtube"],
                        "items": [
                            {"type": "work", "title": "Harmony", "year": 2018}
                        ],
                    },
                ],
            },
            {
                "id": "ads",
                "title": "Advertisements & Ringtones",
                "subsections": [
                    {
                        "id": "ads-pre",
                        "title": "Advertisements — pre-2000",
                        "providers": ["youtube"],
                        "items": [
                            {"type": "work", "title": "Leo Coffee", "year": 1990}
                        ],
                    }
                ],
            },
            {
                "id": "noncreative",
                "title": "Other Work, Institutions & Curation",
                "subsections": [
                    {
                        "id": "initiatives",
                        "title": "Initiatives (Self)",
                        "providers": ["web", "youtube"],
                        "items": [
                            {"type": "work", "title": "KM Music Conservatory"}
                        ],
                    }
                ],
            },
            {
                "id": "videos",
                "title": "Video Song Performances",
                "subsections": [
                    {
                        "id": "videos-film",
                        "title": "Video of Film Songs",
                        "providers": ["youtube"],
                        "items": [
                            {"type": "work", "title": "Bigil — Singappenney", "year": 2019}
                        ],
                    }
                ],
            },
        ]

        quality = build.build_quality(categories)
        labels = {item["label"]: item["missing"] for item in quality["missingLinks"]}

        self.assertEqual(labels, {
            "Roja": ["youtube"],
            "Vande Mataram": ["spotify", "youtube"],
        })

    def test_peddi_is_present_as_multilingual_film_entry(self) -> None:
        source = json.loads((Path(__file__).resolve().parent.parent / "data" / "source" / "01-films.json").read_text(encoding="utf-8"))

        peddi_versions = []
        for subsection in source["subsections"]:
            if subsection.get("type") != "films":
                continue
            for item in subsection.get("items", []):
                versions = item.get("versions", [])
                if any(version.get("title") == "Peddi" for version in versions):
                    peddi_versions = versions
                    break
            if peddi_versions:
                break

        self.assertTrue(peddi_versions, "Peddi should be listed as a film entry")
        self.assertEqual(
            {version["language"] for version in peddi_versions},
            {"Telugu", "Hindi", "Tamil", "Kannada", "Malayalam"},
        )
        self.assertTrue(all(version.get("date") == "04-06-2026" for version in peddi_versions))

    def test_blocked_search_backend_stops_resolution_after_one_failure(self) -> None:
        class BlockedResolver:
            name = "Blocked search"
            available = True

            def __init__(self) -> None:
                self.calls = 0

            def resolve(self, provider, subject):
                self.calls += 1
                raise urllib.error.HTTPError(
                    url="https://duckduckgo.com/html/",
                    code=403,
                    msg="Forbidden",
                    hdrs=None,
                    fp=None,
                )

        categories = [
            {
                "id": "nonfilm",
                "title": "Non-Film Compositions",
                "subsections": [
                    {
                        "id": "singles",
                        "title": "Singles",
                        "providers": ["spotify", "youtubeMusic", "appleMusic", "youtube"],
                        "items": [
                            {
                                "type": "work",
                                "title": "Oh Bosnia",
                                "year": 1996,
                                "providers": ["spotify", "youtubeMusic", "appleMusic", "youtube"],
                            }
                        ],
                    }
                ],
            }
        ]
        blocked = BlockedResolver()
        original_factory = build.create_search_resolver
        build.create_search_resolver = lambda **kwargs: blocked
        stderr = io.StringIO()

        try:
            with contextlib.redirect_stderr(stderr):
                resolved = build.resolve_missing_links(categories, {}, search_engine="duckduckgo")
        finally:
            build.create_search_resolver = original_factory

        self.assertEqual(resolved, 0)
        self.assertEqual(blocked.calls, 1)
        self.assertIn("Skipping provider link resolution: Blocked search returned HTTP 403", stderr.getvalue())
        self.assertNotIn("Stopping provider link resolution after 5 search failures", stderr.getvalue())

    def test_spotify_album_resolution_only_checks_missing_film_spotify_links(self) -> None:
        class FakeSpotifyResolver:
            available = True

            def __init__(self) -> None:
                self.calls = []

            def resolve_album(self, subject):
                self.calls.append(subject["label"])
                return f"https://open.spotify.com/album/{build.slugify(subject['label'])}", "fake query"

        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "films-main",
                        "title": "Films with multi-language releases",
                        "providers": ["spotify", "youtubeMusic"],
                        "items": [
                            {
                                "type": "film",
                                "year": 1994,
                                "versions": [
                                    {
                                        "language": "Tamil",
                                        "title": "Already Linked",
                                        "links": {"spotify": "https://open.spotify.com/album/existing"},
                                        "providers": ["spotify", "youtubeMusic"],
                                    },
                                    {
                                        "language": "Hindi",
                                        "title": "Missing Film",
                                        "providers": ["spotify", "youtubeMusic"],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "id": "nonfilm",
                "title": "Non-Film Compositions",
                "subsections": [
                    {
                        "id": "singles",
                        "title": "Singles",
                        "providers": ["spotify"],
                        "items": [
                            {
                                "type": "work",
                                "title": "Non Film Missing",
                                "providers": ["spotify"],
                            }
                        ],
                    }
                ],
            },
        ]
        cache = {"schemaVersion": 1, "links": {}}
        resolver = FakeSpotifyResolver()

        with contextlib.redirect_stderr(io.StringIO()):
            resolved = build.resolve_missing_spotify_album_links(categories, cache, resolver=resolver)

        self.assertEqual(resolved, 1)
        self.assertEqual(resolver.calls, ["Missing Film"])
        versions = categories[0]["subsections"][0]["items"][0]["versions"]
        self.assertEqual(versions[0]["links"]["spotify"], "https://open.spotify.com/album/existing")
        self.assertEqual(versions[1]["links"]["spotify"], "https://open.spotify.com/album/missing-film")
        self.assertNotIn("links", categories[1]["subsections"][0]["items"][0])

    def test_spotify_album_resolution_logs_progress_for_each_checked_album(self) -> None:
        class FakeSpotifyResolver:
            available = True

            def resolve_album(self, subject):
                if subject["label"] == "Missing Film":
                    return "https://open.spotify.com/album/missing-film", "fake query"
                return None, "fake query"

        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "films-main",
                        "title": "Films with multi-language releases",
                        "providers": ["spotify"],
                        "items": [
                            {
                                "type": "film",
                                "year": 1994,
                                "versions": [
                                    {
                                        "language": "Hindi",
                                        "title": "Missing Film",
                                        "providers": ["spotify"],
                                    },
                                    {
                                        "language": "Tamil",
                                        "title": "No Match Film",
                                        "providers": ["spotify"],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            resolved = build.resolve_missing_spotify_album_links(
                categories,
                {"schemaVersion": 1, "links": {}},
                resolver=FakeSpotifyResolver(),
            )

        output = stderr.getvalue()
        self.assertEqual(resolved, 1)
        self.assertIn("Spotify album resolution: checking 2 missing film Spotify album links.", output)
        self.assertIn("[1/2] Missing Film (Hindi, 1994)", output)
        self.assertIn("resolved https://open.spotify.com/album/missing-film", output)
        self.assertIn("[2/2] No Match Film (Tamil, 1994)", output)
        self.assertIn("no confident album match", output)
        self.assertIn("Spotify album resolution: resolved 1 of 2 checked links.", output)

    def test_spotify_album_resolution_logs_best_rejected_candidate(self) -> None:
        class FakeSpotifyResolver:
            available = True

            def resolve_album(self, subject):
                return build.SpotifyAlbumResolution(
                    url=None,
                    query="fake query",
                    candidate_count=2,
                    best_name="Gandhi Talks",
                    best_score=75,
                    best_url="https://open.spotify.com/album/wrong",
                )

        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "films-main",
                        "title": "Films with multi-language releases",
                        "providers": ["spotify"],
                        "items": [
                            {
                                "type": "film",
                                "year": 2023,
                                "versions": [
                                    {
                                        "language": "Hindi",
                                        "title": "Gandhi Vs Godse – Ek Yudh",
                                        "providers": ["spotify"],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            resolved = build.resolve_missing_spotify_album_links(
                categories,
                {"schemaVersion": 1, "links": {}},
                resolver=FakeSpotifyResolver(),
            )

        output = stderr.getvalue()
        self.assertEqual(resolved, 0)
        self.assertIn("no confident album match; 2 candidates; best rejected: Gandhi Talks (score 75)", output)
        self.assertIn("https://open.spotify.com/album/wrong", output)

    def test_spotify_album_resolution_writes_missing_link_to_source_json(self) -> None:
        class FakeSpotifyResolver:
            available = True

            def resolve_album(self, subject):
                return "https://open.spotify.com/album/missing-film", "fake query"

        source_category = {
            "id": "films",
            "num": "01",
            "title": "Film Compositions",
            "subsections": [
                {
                    "id": "films-main",
                    "num": "1",
                    "title": "Films",
                    "type": "films",
                    "items": [
                        {
                            "type": "film",
                            "year": 1994,
                            "versions": [
                                {
                                    "language": "Tamil",
                                    "title": "Already Linked",
                                    "date": "1994",
                                    "links": {"spotify": "https://open.spotify.com/album/existing"},
                                },
                                {
                                    "language": "Hindi",
                                    "title": "Missing Film",
                                    "date": "1994",
                                },
                            ],
                        }
                    ],
                }
            ],
        }
        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "films-main",
                        "title": "Films",
                        "providers": ["spotify"],
                        "items": [
                            {
                                "type": "film",
                                "year": 1994,
                                "versions": [
                                    {
                                        "language": "Tamil",
                                        "title": "Already Linked",
                                        "links": {"spotify": "https://open.spotify.com/album/existing"},
                                        "providers": ["spotify"],
                                    },
                                    {
                                        "language": "Hindi",
                                        "title": "Missing Film",
                                        "date": "1994",
                                        "providers": ["spotify"],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "01-films.json"
            source_path.write_text(json.dumps(source_category, indent=2) + "\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                resolved = build.resolve_missing_spotify_album_links(
                    categories,
                    {"schemaVersion": 1, "links": {}},
                    resolver=FakeSpotifyResolver(),
                    source_dir=Path(temp_dir),
                )

            saved = json.loads(source_path.read_text(encoding="utf-8"))

        versions = saved["subsections"][0]["items"][0]["versions"]
        self.assertEqual(resolved, 1)
        self.assertEqual(versions[0]["links"]["spotify"], "https://open.spotify.com/album/existing")
        self.assertEqual(versions[1]["links"]["spotify"], "https://open.spotify.com/album/missing-film")

    def test_spotify_album_picker_prefers_matching_rahman_album(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Love You Hamesha",
            "language": "Hindi",
            "year": 1994,
        }
        albums = [
            {
                "name": "Love Songs Forever",
                "album_type": "album",
                "total_tracks": 12,
                "release_date": "2001-01-01",
                "artists": [{"name": "Various Artists"}],
                "external_urls": {"spotify": "https://open.spotify.com/album/wrong"},
            },
            {
                "name": "Love You Hamesha (Original Motion Picture Soundtrack)",
                "album_type": "album",
                "total_tracks": 7,
                "release_date": "2001-01-01",
                "artists": [{"name": "A.R. Rahman"}],
                "external_urls": {"spotify": "https://open.spotify.com/album/right"},
            },
        ]

        selected = build.pick_spotify_album_link(subject, albums)

        self.assertEqual(selected, "https://open.spotify.com/album/right")

    def test_spotify_album_picker_rejects_weak_album_match(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Gandhi Vs Godse – Ek Yudh",
            "language": "Hindi",
            "year": 2023,
        }
        albums = [
            {
                "name": "Gandhi Talks",
                "album_type": "album",
                "total_tracks": 5,
                "release_date": "2023-01-01",
                "artists": [{"name": "A.R. Rahman"}],
                "external_urls": {"spotify": "https://open.spotify.com/album/wrong"},
            }
        ]

        selected = build.pick_spotify_album_link(subject, albums)

        self.assertIsNone(selected)

    def test_spotify_album_picker_rejects_conflicting_language_album(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Roja",
            "language": "Tamil",
            "year": 1992,
            "versionYear": 1992,
        }
        albums = [
            {
                "name": "Roja (Marathi) (Original Motion Picture Soundtrack)",
                "album_type": "album",
                "total_tracks": 6,
                "release_date": "1992-01-01",
                "artists": [{"name": "A.R. Rahman"}],
                "external_urls": {"spotify": "https://open.spotify.com/album/wrong"},
            }
        ]

        selected = build.pick_spotify_album_link(subject, albums)

        self.assertIsNone(selected)

    def test_spotify_album_picker_requires_language_evidence_for_same_title_versions(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Roja",
            "language": "Telugu",
            "year": 1992,
            "versionYear": 1992,
            "languageEvidenceRequired": True,
        }
        albums = [
            {
                "name": "Roja (Original Motion Picture Soundtrack)",
                "album_type": "album",
                "total_tracks": 6,
                "release_date": "1992-01-01",
                "artists": [{"name": "A.R. Rahman"}],
                "external_urls": {"spotify": "https://open.spotify.com/album/ambiguous"},
            }
        ]

        selected = build.pick_spotify_album_link(subject, albums)

        self.assertIsNone(selected)

    def test_link_targets_mark_same_title_multilingual_versions_as_language_ambiguous(self) -> None:
        categories = [
            {
                "id": "films",
                "title": "Film Compositions",
                "subsections": [
                    {
                        "id": "multi",
                        "title": "Films with multi-language releases",
                        "items": [
                            {
                                "type": "film",
                                "year": 1992,
                                "versions": [
                                    {"language": "Tamil", "title": "Roja", "date": "1992"},
                                    {"language": "Telugu", "title": "Roja", "date": "1992"},
                                    {"language": "Hindi", "title": "Roja", "date": "1994"},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        subjects = [subject for subject, _ in build.iter_link_targets(categories)]

        self.assertTrue(all(subject["languageEvidenceRequired"] for subject in subjects))


if __name__ == "__main__":
    unittest.main()
