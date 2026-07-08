#!/usr/bin/env python3
"""Orchestrate fetching, parsing, and updating durban_gov_za.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fetch import download_docx, fetch_region_docs
from generate_mapping import (
    _format_mapping_block,
    build_collection_areas,
    format_python_file,
    replace_mapping_block,
)

DEFAULT_TARGET = (
    Path(__file__).resolve().parents[2]
    / "custom_components/waste_collection_schedule/waste_collection_schedule/source/durban_gov_za.py"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Path to durban_gov_za.py",
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
        help="Do not write files",
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
    block = _format_mapping_block(collection_areas, region_sources)

    total_areas = sum(len(areas) for areas in collection_areas.values())
    print(
        f"Parsed {total_areas} areas across {len(collection_areas)} regions.",
    )

    if args.dry_run:
        print(block)
        return 0

    if not args.target.exists():
        print(f"Target file not found: {args.target}", file=sys.stderr)
        return 1

    sources_path.write_text(
        json.dumps(region_sources, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    changed = replace_mapping_block(args.target, block)
    format_python_file(args.target)
    print("Mapping updated." if changed else "Mapping unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
