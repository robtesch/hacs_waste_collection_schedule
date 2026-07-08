"""Tests for Durban mapping generation helpers."""

from __future__ import annotations

from datetime import date

from generate_mapping import schedule_date_from_sources, schedule_date_from_url


def test_schedule_date_from_url_extracts_publish_date() -> None:
    url = "https://www.durban.gov.za/uploads/0000/6/2025/09/18/inner-west.docx"
    assert schedule_date_from_url(url) == date(2025, 9, 18)


def test_schedule_date_from_url_returns_none_for_local_path() -> None:
    assert (
        schedule_date_from_url("tools/durban_gov_za/downloads/inner_west.docx") is None
    )


def test_schedule_date_from_sources_uses_newest_date() -> None:
    region_sources = {
        "inner_west": "https://www.durban.gov.za/uploads/0000/6/2025/09/18/inner-west.docx",
        "north": "https://www.durban.gov.za/uploads/0000/6/2026/01/15/north-region.docx",
    }
    assert schedule_date_from_sources(region_sources) == date(2026, 1, 15)


def test_schedule_date_from_sources_returns_none_without_urls() -> None:
    assert schedule_date_from_sources({}) is None
