"""Tests for Durban DOCX parsing."""

from __future__ import annotations

from pathlib import Path

from parse_docx import parse_docx_file, slugify

FIXTURES = Path(__file__).parent / "fixtures"
DOWNLOADS = Path(__file__).parent.parent / "downloads"


def test_slugify_normalizes_names() -> None:
    assert slugify("Drummond & Montesseel") == "drummond_montesseel"
    assert slugify("  Hillcrest CBD  ") == "hillcrest_cbd"


def test_parse_outer_west_contains_hillcrest() -> None:
    path = DOWNLOADS / "outer_west.docx"
    if not path.exists():
        path = FIXTURES / "outer_west.docx"
    areas = parse_docx_file(path)
    assert "hillcrest" in areas
    assert areas["hillcrest"]["weekday"] == 0


def test_parse_outer_west_contains_drummond() -> None:
    path = DOWNLOADS / "outer_west.docx"
    if not path.exists():
        path = FIXTURES / "outer_west.docx"
    areas = parse_docx_file(path)
    assert "drummond_montesseel" in areas
    assert areas["drummond_montesseel"]["weekday"] == 2
