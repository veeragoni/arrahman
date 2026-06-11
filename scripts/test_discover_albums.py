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


class StubSpotify:
    def __init__(self, albums_by_id):
        self.albums_by_id = albums_by_id

    def full_albums(self, ids):
        return [self.albums_by_id[i] for i in ids if i in self.albums_by_id]


def curated_target(label, current_spotify=""):
    subject = {
        "categoryId": "films",
        "category": "Film Compositions",
        "subsectionId": "hindi-undubbed",
        "subsection": "Hindi films",
        "entryIndex": 1,
        "type": "work",
        "label": label,
        "language": "",
        "year": None,
        "date": "",
        "versionYear": None,
        "providers": ["spotify", "youtubeMusic", "appleMusic", "youtube"],
    }
    target = {"links": {"spotify": current_spotify} if current_spotify else {}}
    return subject, target


class PromotionTests(unittest.TestCase):
    def _full_album(self):
        return spotify_album(
            id="album1",
            name="Main Vaapas Aaunga (Original Motion Picture Soundtrack)",
            artists=[{"name": "A.R. Rahman"}],
            total_tracks=8,
            external_urls={"spotify": "https://open.spotify.com/album/album1"},
            tracks={"items": [
                {"name": n, "artists": [{"name": "A.R. Rahman"}]}
                for n in ["Vo Nahin", "Kya Kamaal Hai", "Title Track"]
            ]},
        )

    def _single(self, track_names):
        return spotify_album(
            id="single1",
            name='Vo Nahin (From "Main Vaapas Aaunga")',
            album_type="single",
            tracks={"items": [{"name": n, "artists": [{"name": "A.R. Rahman"}]} for n in track_names]},
        )

    def _promote(self, current_spotify, stub_albums):
        album = self._full_album()
        targets = [curated_target("Main Vaapas Aaunga", current_spotify)]
        return discover_albums.promote_album_to_curated(
            StubSpotify(stub_albums), album,
            {"spotify": "https://open.spotify.com/album/album1"},
            targets, dry_run=True,
        )

    def test_promotes_when_curated_entry_has_no_link(self) -> None:
        promoted, subject, reason = self._promote("", {})
        self.assertTrue(promoted, reason)
        self.assertEqual(subject["label"], "Main Vaapas Aaunga")

    def test_replaces_pre_release_single_link(self) -> None:
        single = self._single(['Vo Nahin (From "Main Vaapas Aaunga")'])
        promoted, _, reason = self._promote(
            "https://open.spotify.com/album/single1", {"single1": single}
        )
        self.assertTrue(promoted, reason)

    def test_keeps_single_with_unreleased_song(self) -> None:
        single = self._single(["Unreleased Bonus Song"])
        promoted, _, reason = self._promote(
            "https://open.spotify.com/album/single1", {"single1": single}
        )
        self.assertFalse(promoted)
        self.assertIn("songs not on the album", reason)

    def test_never_replaces_existing_album_link(self) -> None:
        other_album = spotify_album(id="other", album_type="album")
        promoted, _, reason = self._promote(
            "https://open.spotify.com/album/other", {"other": other_album}
        )
        self.assertFalse(promoted)
        self.assertIn("already links a full album", reason)

    def test_unrelated_album_does_not_match(self) -> None:
        album = self._full_album()
        targets = [curated_target("Completely Different Film")]
        promoted, subject, _ = discover_albums.promote_album_to_curated(
            StubSpotify({}), album,
            {"spotify": "https://open.spotify.com/album/album1"},
            targets, dry_run=True,
        )
        self.assertFalse(promoted)
        self.assertIsNone(subject)

    def test_alternate_versions_and_singles_never_promote(self) -> None:
        remix = spotify_album(name="Main Vaapas Aaunga (Lofi Remix)", artists=[{"name": "A.R. Rahman"}])
        single = spotify_album(album_type="single", artists=[{"name": "A.R. Rahman"}])
        targets = [curated_target("Main Vaapas Aaunga")]
        for album in (remix, single):
            promoted, _, _ = discover_albums.promote_album_to_curated(
                StubSpotify({}), album, {"spotify": "https://open.spotify.com/album/x"}, targets, dry_run=True,
            )
            self.assertFalse(promoted)


class YouTubeMusicTests(unittest.TestCase):
    def _payload(self):
        def item(browse_id, title, subtitle_runs):
            return {"musicResponsiveListItemRenderer": {
                "navigationEndpoint": {"browseEndpoint": {"browseId": browse_id}},
                "flexColumns": [
                    {"musicResponsiveListItemFlexColumnRenderer": {"text": {"runs": [{"text": title}]}}},
                    {"musicResponsiveListItemFlexColumnRenderer": {"text": {"runs": [{"text": t} for t in subtitle_runs]}}},
                ],
            }}
        return {"contents": {"sectionListRenderer": {"contents": [
            {"musicShelfRenderer": {"contents": [
                item("MPREb_roja", "Roja (Tamil)", ["EP", " • ", "A.R. Rahman", " • ", "1992"]),
                item("VLPLnotanalbum", "Some Playlist", ["Playlist"]),
                item("MPREb_other", "Unrelated Hits", ["Album", " • ", "Someone Else", " • ", "2010"]),
            ]}},
        ]}}}

    def test_extracts_only_album_browse_ids(self) -> None:
        albums = discover_albums.ytmusic_albums_from_payload(self._payload())
        self.assertEqual([a["browseId"] for a in albums], ["MPREb_roja", "MPREb_other"])
        self.assertEqual(albums[0]["url"], "https://music.youtube.com/browse/MPREb_roja")
        self.assertIn("1992", albums[0]["subtitle"])

    def test_picks_matching_album(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Roja",
            "language": "Tamil",
            "year": 1992,
            "versionYear": 1992,
        }
        albums = discover_albums.ytmusic_albums_from_payload(self._payload())
        self.assertEqual(
            discover_albums.pick_ytmusic_link(subject, albums),
            "https://music.youtube.com/browse/MPREb_roja",
        )

    def test_rejects_wrong_language_and_non_rahman(self) -> None:
        subject = {
            "categoryId": "films",
            "type": "filmVersion",
            "label": "Roja",
            "language": "Hindi",
            "year": 1992,
            "versionYear": 1992,
        }
        albums = discover_albums.ytmusic_albums_from_payload(self._payload())
        # Tamil-tagged album must not satisfy the Hindi version.
        self.assertEqual(discover_albums.pick_ytmusic_link(subject, albums), "")

    def test_query_includes_language(self) -> None:
        subject = {"label": "Roja", "language": "Tamil"}
        self.assertEqual(discover_albums.ytmusic_query(subject), "Roja Tamil A.R. Rahman")


class ArtworkTests(unittest.TestCase):
    def test_apple_lookup_params(self) -> None:
        self.assertEqual(
            discover_albums.apple_lookup_params(
                "https://music.apple.com/in/album/roja-original-motion-picture-soundtrack/1842069592"
            ),
            ("1842069592", "IN"),
        )
        self.assertEqual(discover_albums.apple_lookup_params("https://example.com/x"), ("", ""))

    def test_spotify_album_image_prefers_300px(self) -> None:
        album = {"images": [
            {"url": "https://i.scdn.co/image/big", "width": 640},
            {"url": "https://i.scdn.co/image/medium", "width": 300},
            {"url": "https://i.scdn.co/image/small", "width": 64},
        ]}
        self.assertEqual(discover_albums.spotify_album_image(album), "https://i.scdn.co/image/medium")
        self.assertEqual(discover_albums.spotify_album_image({"images": []}), "")


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
