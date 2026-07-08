"""Generate the COLLECTION_AREAS block for durban_gov_za.py."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from fetch import REGION_TITLES, RegionDoc
from parse_docx import parse_docx_bytes

BEGIN_MARKER = "# BEGIN GENERATED DURBAN AREA MAPPING"
END_MARKER = "# END GENERATED DURBAN AREA MAPPING"
_SCHEDULE_DATE_RE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")


def schedule_date_from_url(url: str) -> date | None:
    """Extract a YYYY/MM/DD publish date from a council DOCX URL path."""
    match = _SCHEDULE_DATE_RE.search(url)
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    return date(year, month, day)


def schedule_date_from_sources(region_sources: dict[str, str]) -> date | None:
    """Return the newest schedule publish date found across source URLs."""
    dates = [
        parsed
        for url in region_sources.values()
        if (parsed := schedule_date_from_url(url)) is not None
    ]
    return max(dates) if dates else None


def format_python_file(path: Path) -> None:
    """Apply repo ruff rules so generated output matches committed style."""
    subprocess.run(["ruff", "check", "--fix", str(path)], check=True)
    subprocess.run(["ruff", "format", str(path)], check=True)


def _format_mapping_block(
    collection_areas: dict[str, dict[str, dict[str, int | str]]],
    region_sources: dict[str, str],
) -> str:
    lines = [
        BEGIN_MARKER,
        "# Generated from:",
    ]
    for region in sorted(collection_areas):
        lines.append(f"#   - {region}: {region_sources.get(region, 'unknown')}")
    schedule_date = schedule_date_from_sources(region_sources)
    if schedule_date is not None:
        lines.append(f"# Based on schedules dated: {schedule_date.isoformat()}")
    lines.append("COLLECTION_AREAS = {")

    for region in sorted(collection_areas):
        lines.append(f'    "{region}": {{')
        areas = collection_areas[region]
        for area_slug in sorted(areas):
            entry = areas[area_slug]
            title = repr(str(entry["title"]))
            weekday = entry["weekday"]
            lines.append(
                f'        "{area_slug}": {{"title": {title}, "weekday": {weekday}}},'
            )
        lines.append("    },")

    lines.append("}")
    lines.append("REGION_TITLES = {")
    for region in sorted(collection_areas):
        title = repr(REGION_TITLES.get(region, region.replace("_", " ").title()))
        lines.append(f'    "{region}": {title},')
    lines.append("}")
    lines.append(END_MARKER)
    return "\n".join(lines)


def build_collection_areas(
    region_docs: list[RegionDoc],
    docx_data: dict[str, bytes],
) -> tuple[dict[str, dict[str, dict[str, int | str]]], dict[str, str]]:
    collection_areas: dict[str, dict[str, dict[str, int | str]]] = {}
    region_sources: dict[str, str] = {}

    for region_doc in region_docs:
        data = docx_data[region_doc.region]
        collection_areas[region_doc.region] = parse_docx_bytes(data)
        region_sources[region_doc.region] = region_doc.url

    return collection_areas, region_sources


def replace_mapping_block(target_path: Path, new_block: str) -> bool:
    content = target_path.read_text(encoding="utf-8")
    start = content.find(BEGIN_MARKER)
    end = content.find(END_MARKER)
    if start == -1 or end == -1:
        raise RuntimeError(f"Mapping markers not found in {target_path}")

    end += len(END_MARKER)
    updated = content[:start] + new_block + content[end:]
    if updated == content:
        return False

    target_path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Path to durban_gov_za.py",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        required=True,
        help="Directory containing downloaded DOCX files named <region>.docx",
    )
    parser.add_argument(
        "--sources-json",
        type=Path,
        help="Optional JSON file mapping region -> source URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print block instead of writing",
    )
    args = parser.parse_args()

    region_docs: list[RegionDoc] = []
    region_sources: dict[str, str] = {}
    docx_data: dict[str, bytes] = {}

    if args.sources_json and args.sources_json.exists():
        region_sources = json.loads(args.sources_json.read_text(encoding="utf-8"))
    else:
        sources_path = args.cache_dir / "source_links.json"
        if sources_path.exists():
            region_sources = json.loads(sources_path.read_text(encoding="utf-8"))

    for docx_path in sorted(args.cache_dir.glob("*.docx")):
        region = docx_path.stem
        docx_data[region] = docx_path.read_bytes()
        region_docs.append(
            RegionDoc(
                region=region,
                title=REGION_TITLES.get(region, region.replace("_", " ").title()),
                url=region_sources.get(region, str(docx_path)),
            )
        )

    collection_areas, built_sources = build_collection_areas(region_docs, docx_data)
    region_sources.update(built_sources)
    block = _format_mapping_block(collection_areas, region_sources)

    if args.dry_run:
        print(block)
        return 0

    changed = replace_mapping_block(args.target, block)
    format_python_file(args.target)
    print(f"Updated {args.target}" if changed else f"No changes in {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
