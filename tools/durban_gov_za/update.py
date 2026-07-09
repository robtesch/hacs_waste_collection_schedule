#!/usr/bin/env python3
"""Fetch council DOCX schedules and regenerate hosted ICS calendars."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fetch import download_docx, fetch_region_docs
from generate_calendars import write_calendars
from generate_mapping import build_collection_areas

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "durban-gov-za"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for index.json and calendars/ (data branch root)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(__file__).parent / "downloads",
        help="Directory for downloaded DOCX files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and parse only; print summary without writing calendars",
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Verify SSL certificates when fetching",
    )
    args = parser.parse_args()

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    sources_path = args.cache_dir / "source_links.json"

    print("Fetching regional DOCX links...")
    region_docs = fetch_region_docs(verify_ssl=args.verify_ssl)
    region_sources = {doc.region: doc.url for doc in region_docs}

    docx_data: dict[str, bytes] = {}
    for region_doc in region_docs:
        print(f"Downloading {region_doc.title}...")
        data = download_docx(region_doc.url, verify_ssl=args.verify_ssl)
        docx_data[region_doc.region] = data
        if not args.dry_run:
            (args.cache_dir / f"{region_doc.region}.docx").write_bytes(data)

    collection_areas, built_sources = build_collection_areas(region_docs, docx_data)
    region_sources.update(built_sources)
    total_areas = sum(len(areas) for areas in collection_areas.values())
    print(
        f"Parsed {total_areas} areas across {len(collection_areas)} regions.",
    )

    if args.dry_run:
        print("Dry run complete; no calendar files written.")
        return 0

    if not args.dry_run:
        sources_path.write_text(
            json.dumps(region_sources, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    changed = write_calendars(collection_areas, region_sources, args.output_dir)
    print("Calendars updated." if changed else "Calendars unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
