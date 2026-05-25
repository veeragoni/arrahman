#!/usr/bin/env python3
"""Split the current legacy discography JSON into normalized source chunks."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = ROOT / "data" / "discography.json"
SOURCE_DIR = ROOT / "data" / "source"

LANGUAGE_FIELDS = [
    ("t", "Tamil"),
    ("te", "Telugu"),
    ("h", "Hindi"),
    ("m", "Malayalam"),
    ("o", "Other"),
]


def compact_empty(value: dict) -> dict:
    return {key: item for key, item in value.items() if item not in ({}, [], "", None)}


def split_title_date(value: str) -> tuple[str, str]:
    title, sep, date = value.partition("•")
    if not sep:
        return value.strip(), ""
    return title.strip(), date.strip()


def normalize_legacy_item(item: dict, subsection_type: str) -> dict:
    if subsection_type == "films":
        versions = []
        for field, language in LANGUAGE_FIELDS:
            if not item.get(field):
                continue
            title, date = split_title_date(item[field])
            versions.append(compact_empty({
                "language": language,
                "title": title,
                "date": date,
            }))

        return compact_empty({
            "type": "film",
            "year": item.get("year", item.get("y")),
            "note": item.get("note", ""),
            "versions": versions,
        })

    return compact_empty({
        "type": "work",
        "title": item.get("title", ""),
        "year": item.get("year", item.get("y")),
        "date": item.get("date", ""),
        "note": item.get("note", ""),
    })


def normalize_category(category: dict) -> dict:
    normalized = {
        "id": category["id"],
        "num": category["num"],
        "title": category["title"],
        "subsections": [],
    }
    if category.get("blurb"):
        normalized["blurb"] = category["blurb"]

    for subsection in category["subsections"]:
        normalized["subsections"].append({
            "id": subsection["id"],
            "num": subsection["num"],
            "title": subsection["title"],
            "type": subsection["type"],
            "items": [
                normalize_legacy_item(item, subsection["type"])
                for item in subsection.get("items", [])
            ],
        })

    return normalized


def main() -> None:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    categories = data.get("categories", [])
    if not categories:
        raise SystemExit("ERROR: no categories found in data/discography.json")

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for index, category in enumerate(categories, start=1):
        source_path = SOURCE_DIR / f"{index:02d}-{category['id']}.json"
        source_path.write_text(
            json.dumps(normalize_category(category), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {source_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
