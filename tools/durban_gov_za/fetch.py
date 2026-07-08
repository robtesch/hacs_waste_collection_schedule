"""Fetch regional DOCX schedule links from durban.gov.za."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests

SCHEDULES_PAGE = "https://www.durban.gov.za/page/refuse-collection-schedules"
BASE_URL = "https://www.durban.gov.za/"

REGION_SLUGS = {
    "inner west": "inner_west",
    "south central": "south_central",
    "north region": "north",
    "outer west": "outer_west",
    "north central": "north_central",
    "south region": "south",
}

REGION_TITLES = {
    "inner_west": "Inner West",
    "south_central": "South Central",
    "north": "North Region",
    "outer_west": "Outer West",
    "north_central": "North Central",
    "south": "South Region",
}


@dataclass(frozen=True)
class RegionDoc:
    region: str
    title: str
    url: str


def _slug_from_link_text(text: str) -> str | None:
    lowered = text.lower()
    for needle, slug in REGION_SLUGS.items():
        if needle in lowered:
            return slug
    return None


def fetch_region_docs(verify_ssl: bool = False) -> list[RegionDoc]:
    """Discover current regional DOCX URLs from the schedules index page."""
    response = requests.get(
        SCHEDULES_PAGE,
        impersonate="chrome",
        timeout=30,
        verify=verify_ssl,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    docs: list[RegionDoc] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if ".docx" not in href.lower():
            continue
        text = anchor.get_text(strip=True)
        region = _slug_from_link_text(text)
        if region is None or region in seen:
            continue
        seen.add(region)
        docs.append(
            RegionDoc(
                region=region,
                title=REGION_TITLES[region],
                url=urljoin(BASE_URL, href),
            )
        )

    if not docs:
        raise RuntimeError("No regional DOCX links found on schedules page")

    return sorted(docs, key=lambda doc: doc.region)


def download_docx(url: str, verify_ssl: bool = False) -> bytes:
    response = requests.get(
        url,
        impersonate="chrome",
        timeout=60,
        verify=verify_ssl,
    )
    response.raise_for_status()
    return response.content


def slugify_filename(region: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", region.lower()).strip("_")
