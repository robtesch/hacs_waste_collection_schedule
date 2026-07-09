"""Tests for Durban ICS calendar generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from generate_calendars import (
    build_area_ics,
    build_index_json,
    first_weekday_on_or_after,
    holidays_on_weekday,
    south_africa_public_holidays,
    write_calendars,
)
from parse_docx import parse_docx_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_first_weekday_on_or_after() -> None:
    ref = date(2025, 1, 6)
    assert first_weekday_on_or_after(ref, 0) == date(2025, 1, 6)
    assert first_weekday_on_or_after(ref, 2) == date(2025, 1, 8)


def test_south_africa_public_holidays_includes_good_friday() -> None:
    holidays = south_africa_public_holidays(2025)
    assert date(2025, 4, 18) in holidays


def test_holidays_on_weekday_filters_by_weekday() -> None:
    monday_holidays = holidays_on_weekday(0, 2025, 2025)
    assert all(day.weekday() == 0 for day in monday_holidays)


def test_build_area_ics_contains_expected_rrules() -> None:
    ics = build_area_ics("outer_west", "hillcrest", 0)
    assert "SUMMARY:General Waste" in ics
    assert "SUMMARY:Recycling" in ics
    assert "SUMMARY:Recycling (odd ISO weeks)" in ics
    assert "RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO" in ics
    assert "RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO" in ics
    assert "EXDATE;VALUE=DATE:" in ics


def test_build_index_json_from_fixture() -> None:
    areas = parse_docx_file(FIXTURES / "outer_west.docx")
    collection_areas = {"outer_west": areas}
    region_sources = {
        "outer_west": (
            "https://www.durban.gov.za/uploads/0000/6/2025/09/18/outer-west.docx"
        ),
    }
    index = build_index_json(collection_areas, region_sources)
    assert index["schedule_date"] == "2025-09-18"
    assert "hillcrest" in index["regions"]["outer_west"]["areas"]


def test_write_calendars_creates_files(tmp_path: Path) -> None:
    areas = parse_docx_file(FIXTURES / "outer_west.docx")
    collection_areas = {"outer_west": areas}
    region_sources = {
        "outer_west": (
            "https://www.durban.gov.za/uploads/0000/6/2025/09/18/outer-west.docx"
        ),
    }

    changed = write_calendars(
        collection_areas, region_sources, tmp_path, validate=False
    )
    assert changed is True
    assert (tmp_path / "index.json").exists()
    assert (tmp_path / "calendars" / "outer_west" / "hillcrest.ics").exists()

    changed_again = write_calendars(
        collection_areas, region_sources, tmp_path, validate=False
    )
    assert changed_again is False
