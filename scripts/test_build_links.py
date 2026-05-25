#!/usr/bin/env python3
"""Unit tests for build-time provider link enrichment."""

from __future__ import annotations

import contextlib
import io
import urllib.error
import unittest

import build


class ProviderLinkResolutionTests(unittest.TestCase):
    def test_default_providers_include_regular_youtube(self) -> None:
        self.assertEqual(
            build.normalize_providers(None),
            ["spotify", "youtubeMusic", "appleMusic", "youtube"],
        )

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


if __name__ == "__main__":
    unittest.main()
