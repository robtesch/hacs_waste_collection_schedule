"""Parse eThekwini regional DOCX schedule tables into area mappings."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from docx import Document

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

AREA_SPLIT_RE = re.compile(r"[,;\n]+")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    slug = SLUG_RE.sub("_", name.lower().strip()).strip("_")
    return slug


def parse_weekday(header: str) -> int | None:
    lowered = header.strip().lower()
    for day_name, weekday in WEEKDAYS.items():
        if lowered.startswith(day_name[:3]) or day_name in lowered:
            return weekday
    return None


def _split_area_names(text: str) -> list[str]:
    names: list[str] = []
    for part in AREA_SPLIT_RE.split(text.strip()):
        part = part.strip(" .")
        if len(part) >= 2:
            names.append(part)
    return names


def parse_docx_bytes(data: bytes) -> dict[str, dict[str, int | str]]:
    """Return area slug -> {title, weekday} from a regional DOCX file."""
    doc = Document(BytesIO(data))
    areas: dict[str, dict[str, int | str]] = {}

    for table in doc.tables:
        if not table.rows:
            continue

        header_cells = [cell.text.strip() for cell in table.rows[0].cells]
        weekdays = [parse_weekday(cell) for cell in header_cells]
        if not any(day is not None for day in weekdays):
            continue

        for row in table.rows[1:]:
            for col_index, cell in enumerate(row.cells):
                if col_index >= len(weekdays):
                    continue
                weekday = weekdays[col_index]
                if weekday is None:
                    continue

                for area_name in _split_area_names(cell.text):
                    base_slug = slugify(area_name)
                    if not base_slug:
                        continue

                    slug = base_slug
                    if slug in areas and areas[slug]["weekday"] != weekday:
                        slug = f"{base_slug}_w{weekday}"

                    areas[slug] = {"title": area_name, "weekday": weekday}

    return areas


def parse_docx_file(path: Path) -> dict[str, dict[str, int | str]]:
    return parse_docx_bytes(path.read_bytes())
