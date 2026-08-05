#!/usr/bin/env python3
"""
Pull event data from an Apify dataset and turn it into an .ics calendar file
that iOS Calendar (or any calendar app) can subscribe to.

Usage:
    APIFY_TOKEN=xxx APIFY_DATASET_ID=yyy python scrape_to_ics.py

Expected shape of each item in the Apify dataset (adjust `parse_event`
below to match whatever fields your actor actually outputs):

    {
        "title": "Jazz Night at The Blue Room",
        "start": "2026-08-12T20:00:00",
        "end": "2026-08-12T23:00:00",       # optional
        "location": "The Blue Room, Vejle",
        "description": "Live jazz, doors at 7:30",
        "url": "https://example.com/events/jazz-night"
    }
"""

import os
import sys
import hashlib
from datetime import datetime
from dateutil import parser as dateparser

from apify_client import ApifyClient
from icalendar import Calendar, Event


def get_events_from_apify(token: str, dataset_id: str) -> list[dict]:
    client = ApifyClient(token)
    dataset = client.dataset(dataset_id)
    items = []
    for item in dataset.iterate_items():
        items.append(item)
    return items


def stable_uid(item: dict) -> str:
    """
    Deterministic UID so re-running the script updates existing events
    instead of duplicating them, as long as title+start stay the same.
    """
    key = f"{item.get('title', '')}-{item.get('start', '')}-{item.get('location', '')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32] + "@event-calendar"


def parse_event(item: dict) -> Event:
    ev = Event()
    ev.add("summary", item.get("title", "Untitled event"))

    start_raw = item.get("start")
    if not start_raw:
        raise ValueError(f"Event missing start time: {item}")
    start_dt = dateparser.parse(start_raw)
    ev.add("dtstart", start_dt)

    end_raw = item.get("end")
    if end_raw:
        ev.add("dtend", dateparser.parse(end_raw))
    # if no end given, leave it out — most calendar apps default to a short duration

    if item.get("location"):
        ev.add("location", item["location"])
    if item.get("description"):
        ev.add("description", item["description"])
    if item.get("url"):
        ev.add("url", item["url"])

    ev.add("uid", stable_uid(item))
    ev.add("dtstamp", datetime.utcnow())
    return ev


def build_calendar(items: list[dict]) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//Local Events Scraper//apify-to-ics//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Local Events")
    cal.add("x-wr-timezone", "Europe/Copenhagen")  # adjust to your timezone

    skipped = 0
    for item in items:
        try:
            cal.add_component(parse_event(item))
        except Exception as e:
            skipped += 1
            print(f"Skipping malformed event: {e}", file=sys.stderr)

    print(f"Built calendar with {len(items) - skipped} events ({skipped} skipped)")
    return cal


def main():
    token = os.environ.get("APIFY_TOKEN")
    dataset_id = os.environ.get("APIFY_DATASET_ID")
    output_path = os.environ.get("ICS_OUTPUT_PATH", "docs/events.ics")

    if not token or not dataset_id:
        print("Set APIFY_TOKEN and APIFY_DATASET_ID environment variables.", file=sys.stderr)
        sys.exit(1)

    items = get_events_from_apify(token, dataset_id)
    cal = build_calendar(items)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(cal.to_ical())

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
