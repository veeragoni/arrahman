#!/usr/bin/env python3
"""Audit JSON source data against the source PDFs.

The source PDFs are generated from Google Sheets. They contain selectable text,
but the standard Python environment for this project intentionally has no PDF
dependencies. This script implements the small subset of PDF text extraction we
need for these sheets: Flate streams, Type0 fonts with ToUnicode CMaps, and
Tj/TJ text operators with text matrix positions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "data" / "source"
FILM_PDF = SOURCE_DIR / "ARRahman Discography Table - Sheet 1 - FILM.pdf"
FILM_JSON = SOURCE_DIR / "01-films.json"


@dataclass(frozen=True)
class TextItem:
    x: float
    y: float
    text: str


LANGUAGE_COLUMNS = [
    (0, 451, "Tamil"),
    (451, 1004, "Telugu"),
    (1004, 1461, "Hindi"),
    (1461, 1925, "Malayalam"),
    (1925, 2422, "Other"),
]

LANGUAGE_SUFFIXES = {
    "arabic",
    "english",
    "kannada",
    "malayalam",
    "marathi",
    "persian",
    "urdu",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def pdf_objects(raw: bytes) -> dict[int, bytes]:
    return {
        int(match.group(1)): match.group(2)
        for match in re.finditer(rb"\b(\d+)\s+0\s+obj\b(.*?)\bendobj\b", raw, re.S)
    }


def flate_streams(objects: dict[int, bytes]) -> dict[int, bytes]:
    streams: dict[int, bytes] = {}
    for object_id, body in objects.items():
        stream_match = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
        if not stream_match:
            continue
        try:
            streams[object_id] = zlib.decompress(stream_match.group(1))
        except zlib.error:
            continue
    return streams


def parse_cmap(cmap_text: str) -> dict[int, str]:
    mapping: dict[int, str] = {}

    for block in re.findall(r"beginbfchar\s*(.*?)\s*endbfchar", cmap_text, re.S):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            mapping[int(src, 16)] = chr(int(dst, 16))

    for block in re.findall(r"beginbfrange\s*(.*?)\s*endbfrange", cmap_text, re.S):
        for src_start, src_end, values in re.findall(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]",
            block,
            re.S,
        ):
            start = int(src_start, 16)
            end = int(src_end, 16)
            dst_values = re.findall(r"<([0-9A-Fa-f]+)>", values)
            for offset, code in enumerate(range(start, end + 1)):
                if offset < len(dst_values):
                    mapping[code] = chr(int(dst_values[offset], 16))

        block_without_arrays = re.sub(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[.*?\]",
            "",
            block,
            flags=re.S,
        )
        for src_start, src_end, dst_start in re.findall(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>",
            block_without_arrays,
        ):
            start = int(src_start, 16)
            end = int(src_end, 16)
            base = int(dst_start, 16)
            for code in range(start, end + 1):
                mapping[code] = chr(base + code - start)

    return mapping


def find_font_maps(objects: dict[int, bytes], streams: dict[int, bytes]) -> dict[str, dict[int, str]]:
    resource_candidates = [
        body
        for body in objects.values()
        if b"/Font" in body and b"/Font1" in body and b"/ToUnicode" not in body
    ]
    if not resource_candidates:
        fail("could not locate PDF font resources")

    resources = max(resource_candidates, key=len)
    font_refs = {
        name.decode("ascii"): int(object_id)
        for name, object_id in re.findall(rb"/(Font\d+)\s+(\d+)\s+0\s+R", resources)
    }

    font_maps: dict[str, dict[int, str]] = {}
    for font_name, object_id in font_refs.items():
        font_body = objects.get(object_id, b"")
        cmap_ref = re.search(rb"/ToUnicode\s+(\d+)\s+0\s+R", font_body)
        if not cmap_ref:
            continue
        cmap_stream = streams.get(int(cmap_ref.group(1)))
        if not cmap_stream:
            continue
        font_maps[font_name] = parse_cmap(cmap_stream.decode("latin1"))

    if not font_maps:
        fail("could not decode PDF font maps")
    return font_maps


def unescape_literal_string(value: bytes) -> bytes:
    escapes = {
        ord("n"): 10,
        ord("r"): 13,
        ord("t"): 9,
        ord("b"): 8,
        ord("f"): 12,
        ord("("): 40,
        ord(")"): 41,
        ord("\\"): 92,
    }
    output = bytearray()
    index = 0
    while index < len(value):
        byte = value[index]
        if byte == 92 and index + 1 < len(value):
            index += 1
            output.append(escapes.get(value[index], value[index]))
        else:
            output.append(byte)
        index += 1
    return bytes(output)


def decode_text_bytes(value: bytes, cmap: dict[int, str]) -> str:
    raw = unescape_literal_string(value)
    chars = []
    for index in range(0, len(raw) - 1, 2):
        code = (raw[index] << 8) + raw[index + 1]
        chars.append(cmap.get(code, ""))
    return "".join(chars)


def extract_pdf_text_items(path: Path) -> list[TextItem]:
    raw = path.read_bytes()
    objects = pdf_objects(raw)
    streams = flate_streams(objects)
    font_maps = find_font_maps(objects, streams)
    content_streams = [stream for stream in streams.values() if b"BT" in stream]
    if not content_streams:
        fail(f"{path.name} has no text content stream")

    content = max(content_streams, key=len)
    items: list[TextItem] = []
    for block in re.findall(rb"BT\s*(.*?)\s*ET", content, re.S):
        font_match = re.search(rb"/(Font\d+)\s+[-0-9.]+\s+Tf", block)
        matrix_match = re.search(
            rb"([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+([-0-9.]+)\s+Tm",
            block,
        )
        if not font_match or not matrix_match:
            continue

        cmap = font_maps.get(font_match.group(1).decode("ascii"))
        if not cmap:
            continue
        text = "".join(
            decode_text_bytes(part, cmap)
            for part in re.findall(rb"\((.*?)\)", block, re.S)
        ).strip()
        if text:
            items.append(TextItem(float(matrix_match.group(5)), float(matrix_match.group(6)), clean_text(text)))

    return sorted(items, key=lambda item: (item.y, item.x))


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def column_language(x: float) -> str | None:
    for start, end, language in LANGUAGE_COLUMNS:
        if start <= x < end:
            return language
    return None


def normalize_date(value: str) -> str:
    value = clean_text(value)
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:2]}-{value[2:4]}-{value[4:]}"
    return value


def entry_year(date: str) -> int | None:
    match = re.search(r"(19|20)\d{2}", date)
    return int(match.group(0)) if match else None


def parse_pdf_entry(text: str, language: str) -> dict[str, str] | None:
    value = clean_text(text).rstrip("*^")
    match = re.match(r"^(.*?)\s*[\(\[]\s*([^\)\]]*(?:19|20)\d{2}[^\)\]]*)[\)\]]\s*(.*)$", value)
    if match:
        title = clean_text(match.group(1))
        date = normalize_date(match.group(2))
        suffix = clean_text(match.group(3))

        if suffix:
            stripped_suffix = suffix.strip("- ")
            if language == "Other" and stripped_suffix.lower() in LANGUAGE_SUFFIXES:
                title = f"{title} ({stripped_suffix})"
            elif language != "Other" and stripped_suffix.lower() == language.lower():
                pass
            elif suffix.startswith("-"):
                title = clean_text(f"{title} {suffix}")
            else:
                title = clean_text(f"{title} {stripped_suffix}")
    else:
        match = re.match(r"^(.*?)\s*[\(\[]\s*([^\)\]]+?)\s*[\)\]]\s*((?:19|20)\d{2})\s*(.*)$", value)
        if not match:
            return None
        title = clean_text(match.group(1))
        suffix = clean_text(match.group(2)).strip("- ")
        date = normalize_date(match.group(3))
        tail = clean_text(match.group(4))
        if language == "Other" and suffix.lower() in LANGUAGE_SUFFIXES:
            title = f"{title} ({suffix})"
        elif suffix.lower() != language.lower():
            title = clean_text(f"{title} {suffix}")
        if tail:
            title = clean_text(f"{title} {tail}")

    return {
        "language": language,
        "title": title,
        "date": date,
    }


def is_film_main_cell(item: TextItem) -> bool:
    if item.y < 90 or item.x >= 2422:
        return False
    if re.search(r"Edit|©|Page|GOPAL|Based on|Following projects|FORTHCOMING", item.text, re.I):
        return False
    return column_language(item.x) is not None and parse_pdf_entry(item.text, column_language(item.x) or "") is not None


def film_main_from_pdf() -> list[dict]:
    row_groups: list[tuple[float, list[tuple[float, dict[str, str]]]]] = []
    for item in extract_pdf_text_items(FILM_PDF):
        if not is_film_main_cell(item):
            continue
        language = column_language(item.x)
        if not language:
            continue
        entry = parse_pdf_entry(item.text, language)
        if not entry:
            continue

        if row_groups and abs(item.y - row_groups[-1][0]) <= 3.0:
            row_y, row_entries = row_groups[-1]
            row_entries.append((item.x, entry))
            row_groups[-1] = ((row_y + item.y) / 2, row_entries)
        else:
            row_groups.append((item.y, [(item.x, entry)]))

    films: list[dict] = []
    for _, row_entries in row_groups:
        versions = [entry for _, entry in sorted(row_entries, key=lambda pair: pair[0])]
        year = entry_year(versions[0].get("date", "")) if versions else None
        if not versions or not year:
            continue
        films.append({
            "type": "film",
            "year": year,
            "versions": versions,
        })
    return films


def load_film_source() -> dict:
    return json.loads(FILM_JSON.read_text(encoding="utf-8"))


def find_subsection(category: dict, subsection_id: str) -> dict:
    for subsection in category.get("subsections", []):
        if subsection.get("id") == subsection_id:
            return subsection
    fail(f"missing subsection {subsection_id}")


def comparable_film_main(items: list[dict]) -> list[dict]:
    comparable = []
    for item in items:
        comparable.append({
            "year": item.get("year"),
            "versions": [
                {
                    "language": version.get("language"),
                    "title": clean_text(version.get("title", "")),
                    "date": clean_text(version.get("date", "")),
                }
                for version in item.get("versions", [])
            ],
        })
    return comparable


LANGUAGE_SORT_ORDER = {
    language: index
    for index, (_, _, language) in enumerate(LANGUAGE_COLUMNS)
}


def film_main_release_identity(items: list[dict]) -> list[dict]:
    identities = []
    for item in items:
        versions = [
            {
                "language": version.get("language"),
                "date": clean_text(version.get("date", "")),
            }
            for version in item.get("versions", [])
        ]
        identities.append({
            "year": item.get("year"),
            "versions": sorted(
                versions,
                key=lambda version: (
                    LANGUAGE_SORT_ORDER.get(version.get("language"), len(LANGUAGE_SORT_ORDER)),
                    version.get("date", ""),
                ),
            ),
        })
    return identities


def has_source_citation(item: dict) -> bool:
    if item.get("sources"):
        return True
    return any(version.get("sources") for version in item.get("versions", []))


def pdf_audited_film_main_items(items: list[dict]) -> list[dict]:
    return [item for item in items if not has_source_citation(item)]


def audit_film_main() -> list[str]:
    expected = comparable_film_main(film_main_from_pdf())
    source_items = find_subsection(load_film_source(), "films-main").get("items", [])
    actual = comparable_film_main(pdf_audited_film_main_items(source_items))
    expected_identity = film_main_release_identity(expected)
    actual_identity = film_main_release_identity(actual)
    if expected_identity == actual_identity:
        return []

    errors = [f"films-main differs from {FILM_PDF.name}: expected {len(expected)} rows, found {len(actual)} rows"]
    for index, (expected_item, actual_item) in enumerate(zip(expected_identity, actual_identity), start=1):
        if expected_item != actual_item:
            errors.append(f"first mismatch at films-main[{index}]")
            errors.append(f"  expected: {json.dumps(expected_item, ensure_ascii=False)}")
            errors.append(f"  actual:   {json.dumps(actual_item, ensure_ascii=False)}")
            break
    if len(expected) != len(actual):
        errors.append(f"row count mismatch: expected {len(expected)}, found {len(actual)}")
    return errors


def sync_film_main() -> None:
    category = load_film_source()
    subsection = find_subsection(category, "films-main")
    subsection["items"] = film_main_from_pdf()
    FILM_JSON.write_text(json.dumps(category, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-film-main", action="store_true", help="rewrite films-main from the film PDF")
    parser.add_argument("--dump-film-main", action="store_true", help="print parsed films-main rows")
    args = parser.parse_args()

    if args.dump_film_main:
        print(json.dumps(film_main_from_pdf(), ensure_ascii=False, indent=2))
        return

    if args.sync_film_main:
        sync_film_main()

    errors = audit_film_main()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    print("OK: film main table matches source PDF")


if __name__ == "__main__":
    main()
