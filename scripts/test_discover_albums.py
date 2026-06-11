#!/usr/bin/env python3
"""Unit tests for weekly release discovery and Apple Music link resolution."""

from __future__ import annotations

import unittest

import discover_albums


def spotify_album(**overrides):
    album = {
        "id": "abc123",
        "name": "Tere Ishk Mein (Original Motion Picture Soundtrack)",
        "album_type": "album",
        "release_date": "2025-11-21",
        "release_date_precision": "day",
        "external_urls": {"spotify": "https://open.spotify.com/album/abc123"},
        "external_ids": {"upc": "190000000000"},
        "tracks": {"items": [{"name": "Title Track"}]},
    }
    album.update(overrides)
    return album


class CleanAppleUrlTests(unittest.TestCase):
    def test_strips_tracking_params(self) -> None:
        self.assertEqual(
            discover_albums.clean_apple_url(
                "https://music.apple.com/in/album/tere-ishk-mein/1734620250?uo=4"
            ),
            "https://music.apple.com/in/album/tere-ishk-mein/1734620250",
        )

    def test_rejects_non_apple_hosts(self) -> None:
        self.assertEqual(discover_albums.clean_apple_url("https://example.com/album/x"), "")
        self.assertEqual(discover_albums.clean_apple_url(""), "")
        self.assertEqual(discover_albums.clean_apple_url(None), "")


class ItunesCollectionTests(unittest.TestCase):
    def test_filters_to_collections_with_links(self) -> None:
        payload = {
            "results": [
                {"wrapperType": "artist", "artistName": "A.R. Rahman"},
                {
                    "wrapperType": "collection",
                    "collectionName": "Roja",
                    "collectionViewUrl": "https://music.apple.com/in/album/roja/1",
                },
                {"wrapperType": "collection", "collectionName": "No URL"},
            ]
        }
        collections = discover_albums.itunes_collections(payload)
        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0]["collectionName"], "Roja")


class AppleTermSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Ponniyin Selvan Part - 1",
            "language": "Tamil",
            "year": 2022,
            "versionYear": 2022,
        }

    def test_picks_matching_soundtrack(self) -> None:
        results = [
            {
                "collectionName": "Ponniyin Selvan Part - 1 (Original Motion Picture Soundtrack)",
                "artistName": "A.R. Rahman",
                "releaseDate": "2022-09-05T07:00:00Z",
                "collectionViewUrl": "https://music.apple.com/in/album/ps1/1734620250?uo=4",
            },
            {
                "collectionName": "Unrelated Hits",
                "artistName": "Someone Else",
                "releaseDate": "2010-01-01T07:00:00Z",
                "collectionViewUrl": "https://music.apple.com/in/album/other/2",
            },
        ]
        self.assertEqual(
            discover_albums.pick_apple_term_search_link(self.subject, results),
            "https://music.apple.com/in/album/ps1/1734620250",
        )

    def test_requires_rahman_in_result(self) -> None:
        results = [
            {
                "collectionName": "Ponniyin Selvan Part - 1",
                "artistName": "Cover Band",
                "releaseDate": "2022-09-05T07:00:00Z",
                "collectionViewUrl": "https://music.apple.com/in/album/cover/3",
            }
        ]
        self.assertEqual(discover_albums.pick_apple_term_search_link(self.subject, results), "")

    def test_rejects_wrong_language_release(self) -> None:
        results = [
            {
                "collectionName": "Ponniyin Selvan Part - 1 (Telugu) [Original Motion Picture Soundtrack]",
                "artistName": "A.R. Rahman",
                "releaseDate": "2022-09-05T07:00:00Z",
                "collectionViewUrl": "https://music.apple.com/in/album/ps1-telugu/4",
            }
        ]
        self.assertEqual(discover_albums.pick_apple_term_search_link(self.subject, results), "")

    def test_below_minimum_score_is_rejected(self) -> None:
        results = [
            {
                "collectionName": "Ponniyin Selvan Part - 1",
                "artistName": "A.R. Rahman",
                "collectionViewUrl": "https://music.apple.com/in/album/ps1/5",
            }
        ]
        self.assertEqual(
            discover_albums.pick_apple_term_search_link(self.subject, results, minimum_score=10_000),
            "",
        )


class ReleaseEntryTests(unittest.TestCase):
    def test_builds_entry_with_links_and_date(self) -> None:
        entry = discover_albums.build_release_entry(
            spotify_album(),
            apple_url="https://music.apple.com/in/album/tere-ishk-mein/999",
        )
        self.assertEqual(entry["type"], "work")
        self.assertEqual(entry["year"], 2025)
        self.assertEqual(entry["date"], "21-11-2025")
        self.assertEqual(entry["links"]["spotify"], "https://open.spotify.com/album/abc123")
        self.assertEqual(entry["links"]["appleMusic"], "https://music.apple.com/in/album/tere-ishk-mein/999")
        self.assertEqual(entry["sources"], ["https://open.spotify.com/album/abc123"])

    def test_year_precision_omits_date(self) -> None:
        entry = discover_albums.build_release_entry(
            spotify_album(release_date="2025", release_date_precision="year")
        )
        self.assertEqual(entry["year"], 2025)
        self.assertNotIn("date", entry)

    def test_note_includes_detected_language_and_single(self) -> None:
        album = spotify_album(
            name="Sukoon (From Tere Ishk Mein) [Hindi]",
            album_type="single",
        )
        note = discover_albums.release_note(album)
        self.assertIn("Hindi", note)
        self.assertIn("Single", note)
        self.assertIn("Auto-added", note)


class DedupeTests(unittest.TestCase):
    def test_matches_existing_spotify_url(self) -> None:
        album = spotify_album()
        self.assertTrue(
            discover_albums.is_existing_release(
                album, {"https://open.spotify.com/album/abc123"}, []
            )
        )

    def test_matches_curated_short_title_same_year(self) -> None:
        album = spotify_album()
        labels = [("Tere Ishk Mein", 2025)]
        self.assertTrue(discover_albums.is_existing_release(album, set(), labels))

    def test_same_title_distant_year_is_new(self) -> None:
        album = spotify_album()
        labels = [("Tere Ishk Mein", 2010)]
        self.assertFalse(discover_albums.is_existing_release(album, set(), labels))

    def test_unrelated_album_is_new(self) -> None:
        album = spotify_album(name="Completely Different Album")
        labels = [("Tere Ishk Mein", 2025)]
        self.assertFalse(discover_albums.is_existing_release(album, set(), labels))


class ClassifyAlbumTests(unittest.TestCase):
    def _album_with_tracks(self, track_artists, name="Some Album"):
        return spotify_album(
            name=name,
            tracks={"items": [
                {"name": f"Track {i}", "artists": [{"name": artist}]}
                for i, artist in enumerate(track_artists)
            ]},
        )

    def test_accepts_album_where_rahman_dominates(self) -> None:
        album = self._album_with_tracks(["A.R. Rahman"] * 8)
        ok, reason = discover_albums.classify_album(album)
        self.assertTrue(ok, reason)

    def test_rejects_multi_composer_compilation(self) -> None:
        album = self._album_with_tracks(["A.R. Rahman"] * 4 + ["Mani Sharma"] * 8)
        ok, reason = discover_albums.classify_album(album)
        self.assertFalse(ok)
        self.assertIn("4/12", reason)

    def test_rejects_album_without_track_data(self) -> None:
        ok, _ = discover_albums.classify_album(spotify_album(tracks={"items": []}))
        self.assertFalse(ok)


class AlternateVersionRoutingTests(unittest.TestCase):
    def test_remix_and_lofi_route_to_versions_subsection(self) -> None:
        for name in (
            "Yenge Enathu Kavithai - Afro DnB",
            "Anbae Idhu Nejam – Lofi",
            "Nenjukkule (Instrumental)",
            "Kadhal Sadugudu - Unplugged",
            "Nisa Risa (Re Imagined)",
        ):
            self.assertEqual(
                discover_albums.target_subsection_id(name),
                discover_albums.VERSIONS_SUBSECTION_ID,
                name,
            )

    def test_regular_soundtrack_routes_to_main_subsection(self) -> None:
        self.assertEqual(
            discover_albums.target_subsection_id("Main Vaapas Aaunga (Original Motion Picture Soundtrack)"),
            discover_albums.MAIN_SUBSECTION_ID,
        )

    def test_default_category_has_both_subsections(self) -> None:
        category = discover_albums.load_new_releases_category(
            discover_albums.NEW_RELEASES_PATH.parent / "does-not-exist.json"
        )
        ids = [subsection["id"] for subsection in category["subsections"]]
        self.assertEqual(
            ids,
            [discover_albums.MAIN_SUBSECTION_ID, discover_albums.VERSIONS_SUBSECTION_ID],
        )


class SubsumptionTests(unittest.TestCase):
    def _single(self, track_names, name="Sukoon (From \"Tere Ishk Mein\") - Single", album_id="single1"):
        return spotify_album(
            id=album_id,
            name=name,
            album_type="single",
            tracks={"items": [{"name": n, "artists": [{"name": "A.R. Rahman"}]} for n in track_names]},
        )

    def _full_album(self, track_names, album_id="album1"):
        return spotify_album(
            id=album_id,
            name="Tere Ishk Mein (Original Motion Picture Soundtrack)",
            album_type="album",
            tracks={"items": [{"name": n, "artists": [{"name": "A.R. Rahman"}]} for n in track_names]},
        )

    def test_single_contained_in_album_is_subsumed(self) -> None:
        single = self._single(['Sukoon (From "Tere Ishk Mein")'])
        album = self._full_album(["Sukoon", "Title Track"])
        self.assertTrue(discover_albums.single_subsumed_by_album(single, album))

    def test_different_version_single_is_kept(self) -> None:
        single = self._single(["Sukoon - Lofi"], name="Sukoon (Lofi)")
        album = self._full_album(["Sukoon", "Title Track"])
        self.assertFalse(discover_albums.single_subsumed_by_album(single, album))

    def test_album_never_subsumed_by_album(self) -> None:
        album_a = self._full_album(["Sukoon"], album_id="a")
        album_b = self._full_album(["Sukoon", "More"], album_id="b")
        self.assertFalse(discover_albums.single_subsumed_by_album(album_a, album_b))

    def test_from_hint_slugs_extracted(self) -> None:
        single = self._single(['Sukoon (From "Tere Ishk Mein")'])
        self.assertIn("tere-ishk-mein", discover_albums.from_hint_slugs(single))


class SpotifyHelpersTests(unittest.TestCase):
    def test_album_id_from_url(self) -> None:
        self.assertEqual(
            discover_albums.spotify_album_id_from_url("https://open.spotify.com/album/1yhVL?si=x"),
            "1yhVL",
        )
        self.assertEqual(discover_albums.spotify_album_id_from_url("https://example.com"), "")
        self.assertEqual(discover_albums.spotify_album_id_from_url(None), "")

    def test_release_date_parts(self) -> None:
        year, day = discover_albums.spotify_release_date_parts(spotify_album())
        self.assertEqual((year, day), (2025, "21-11-2025"))
        year, day = discover_albums.spotify_release_date_parts(
            spotify_album(release_date="2025-11", release_date_precision="month")
        )
        self.assertEqual((year, day), (2025, ""))


class NewReleasesCategoryTests(unittest.TestCase):
    def test_default_category_passes_site_validation_shape(self) -> None:
        category = discover_albums.load_new_releases_category(
            discover_albums.NEW_RELEASES_PATH.parent / "does-not-exist.json"
        )
        self.assertEqual(category["id"], "new-releases")
        self.assertEqual(category["subsections"][0]["type"], "list")
        required_category_keys = {"id", "num", "title", "subsections"}
        required_subsection_keys = {"id", "num", "title", "type", "items"}
        self.assertTrue(required_category_keys <= category.keys())
        self.assertTrue(required_subsection_keys <= category["subsections"][0].keys())

    def test_entries_sorted_newest_first(self) -> None:
        category = discover_albums.load_new_releases_category(
            discover_albums.NEW_RELEASES_PATH.parent / "does-not-exist.json"
        )
        category["subsections"][0]["items"] = [
            {"type": "work", "title": "Old", "year": 2024, "date": "01-01-2024", "links": {}},
            {"type": "work", "title": "New", "year": 2026, "date": "15-05-2026", "links": {}},
        ]
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "06-new-releases.json"
            discover_albums.save_new_releases_category(category, path)
            saved = json.loads(path.read_text(encoding="utf-8"))
        titles = [item["title"] for item in saved["subsections"][0]["items"]]
        self.assertEqual(titles, ["New", "Old"])


if __name__ == "__main__":
    unittest.main()
