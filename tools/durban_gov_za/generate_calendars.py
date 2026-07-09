"""Generate ICS calendars and index.json for eThekwini collection areas."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from dateutil.easter import easter
from fetch import REGION_TITLES
from generate_mapping import schedule_date_from_sources

REFERENCE_MONDAY = date(2025, 1, 6)
BYDAY = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
EXPECTED_REGIONS = 6
MIN_AREAS = 1500
HOLIDAY_YEARS_AHEAD = 2

CollectionAreas = dict[str, dict[str, dict[str, int | str]]]


def south_africa_public_holidays(year: int) -> set[date]:
    """Return observed South African public holidays for the given year."""
    holidays: set[date] = set()

    def observe(day: date) -> date:
        if day.weekday() == 5:
            return day + timedelta(days=2)
        if day.weekday() == 6:
            return day + timedelta(days=1)
        return day

    for month, day in (
        (1, 1),
        (3, 21),
        (4, 27),
        (5, 1),
        (6, 16),
        (8, 9),
        (9, 24),
        (12, 16),
        (12, 25),
        (12, 26),
    ):
        holidays.add(observe(date(year, month, day)))

    good_friday = easter(year) - timedelta(days=2)
    family_day = easter(year) + timedelta(days=1)
    holidays.update({good_friday, family_day})
    return holidays


def holidays_on_weekday(weekday: int, from_year: int, to_year: int) -> list[date]:
    """Return public holidays falling on the given weekday between years."""
    dates: list[date] = []
    for year in range(from_year, to_year + 1):
        for holiday in south_africa_public_holidays(year):
            if holiday.weekday() == weekday:
                dates.append(holiday)
    return sorted(dates)


def first_weekday_on_or_after(ref: date, weekday: int) -> date:
    days_ahead = weekday - ref.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


def _format_ics_date(day: date) -> str:
    return day.strftime("%Y%m%d")


def _format_exdate(dates: list[date]) -> str:
    if not dates:
        return ""
    joined = ",".join(_format_ics_date(day) for day in dates)
    return f"EXDATE;VALUE=DATE:{joined}\n"


def _build_vevent(
    uid: str,
    summary: str,
    start: date,
    byday: str,
    interval: int = 1,
    exdates: list[date] | None = None,
) -> str:
    end = start + timedelta(days=1)
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"SUMMARY:{summary}",
        f"DTSTART;VALUE=DATE:{_format_ics_date(start)}",
        f"DTEND;VALUE=DATE:{_format_ics_date(end)}",
        f"RRULE:FREQ=WEEKLY;INTERVAL={interval};BYDAY={byday}",
    ]
    if exdates:
        lines.append(_format_exdate(exdates).rstrip("\n"))
    lines.append("END:VEVENT")
    return "\n".join(lines)


def build_area_ics(region: str, area: str, weekday: int) -> str:
    """Build a single-area ICS calendar with general and recycling collections."""
    byday = BYDAY[weekday]
    start = first_weekday_on_or_after(REFERENCE_MONDAY, weekday)
    odd_start = start + timedelta(days=7)
    current_year = date.today().year
    exdates = holidays_on_weekday(
        weekday, current_year, current_year + HOLIDAY_YEARS_AHEAD
    )

    events = [
        _build_vevent(
            uid=f"durban-{region}-{area}-general-waste@robtesch.github",
            summary="General Waste",
            start=start,
            byday=byday,
        ),
        _build_vevent(
            uid=f"durban-{region}-{area}-recycling-even@robtesch.github",
            summary="Recycling",
            start=start,
            byday=byday,
            interval=2,
            exdates=exdates,
        ),
        _build_vevent(
            uid=f"durban-{region}-{area}-recycling-odd@robtesch.github",
            summary="Recycling (odd ISO weeks)",
            start=odd_start,
            byday=byday,
            interval=2,
            exdates=exdates,
        ),
    ]

    body = "\n".join(events)
    return (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//robtesch//eThekwini Waste Collection//EN\n"
        "CALSCALE:GREGORIAN\n"
        f"{body}\n"
        "END:VCALENDAR\n"
    )


def build_index_json(
    collection_areas: CollectionAreas,
    region_sources: dict[str, str],
) -> dict[str, object]:
    schedule_date = schedule_date_from_sources(region_sources)
    regions: dict[str, object] = {}
    for region in sorted(collection_areas):
        areas = collection_areas[region]
        regions[region] = {
            "title": REGION_TITLES.get(region, region.replace("_", " ").title()),
            "areas": {
                slug: {"title": str(entry["title"])}
                for slug, entry in sorted(areas.items())
            },
        }

    payload: dict[str, object] = {
        "source_urls": {key: region_sources[key] for key in sorted(region_sources)},
        "regions": regions,
    }
    if schedule_date is not None:
        payload["schedule_date"] = schedule_date.isoformat()
    return payload


def validate_collection_areas(collection_areas: CollectionAreas) -> int:
    if len(collection_areas) != EXPECTED_REGIONS:
        msg = f"expected {EXPECTED_REGIONS} regions, got {len(collection_areas)}"
        raise ValueError(msg)

    total_areas = sum(len(areas) for areas in collection_areas.values())
    if total_areas < MIN_AREAS:
        msg = f"expected at least {MIN_AREAS} areas, got {total_areas}"
        raise ValueError(msg)
    return total_areas


def write_calendars(
    collection_areas: CollectionAreas,
    region_sources: dict[str, str],
    output_dir: Path,
    *,
    validate: bool = True,
) -> bool:
    """Write index.json and per-area ICS files. Returns True if content changed."""
    if validate:
        validate_collection_areas(collection_areas)
    output_dir = output_dir.resolve()
    calendars_dir = output_dir / "calendars"

    index_path = output_dir / "index.json"
    new_index = build_index_json(collection_areas, region_sources)
    index_text = json.dumps(new_index, indent=2, sort_keys=True) + "\n"

    changed = False
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != index_text:
        changed = True

    for region, areas in collection_areas.items():
        region_dir = calendars_dir / region
        for area_slug, entry in areas.items():
            weekday = int(entry["weekday"])
            ics_path = region_dir / f"{area_slug}.ics"
            ics_text = build_area_ics(region, area_slug, weekday)
            if (
                not ics_path.exists()
                or ics_path.read_text(encoding="utf-8") != ics_text
            ):
                changed = True

    if not changed:
        return False

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_text, encoding="utf-8")

    for region, areas in collection_areas.items():
        region_dir = calendars_dir / region
        region_dir.mkdir(parents=True, exist_ok=True)
        for area_slug, entry in areas.items():
            weekday = int(entry["weekday"])
            ics_path = region_dir / f"{area_slug}.ics"
            ics_path.write_text(
                build_area_ics(region, area_slug, weekday),
                encoding="utf-8",
            )

    return True
