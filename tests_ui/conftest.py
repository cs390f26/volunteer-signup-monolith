"""Shared setup for Playwright acceptance tests.

Assumes DynamoDB Local and Flask are already running on the usual ports
(see docs/development.md). This file only checks that the app is healthy, exposes
base_url for pytest-playwright, and provides data fixtures via Database.
"""

import urllib.error
import urllib.request

import pytest

from volunteer_signup.db import Database

# Same host/port as python -m volunteer_signup.app (app.run(port=5000)).
BASE_URL = "http://127.0.0.1:5000"

FOOD_DRIVE = {
    "event": {
        "eventId": "m3n8kp2w",
        "createdAt": "2026-09-20T10:00:00.000Z",
        "name": "Food Drive Sorting",
        "description": "Sort and box donations at the campus food pantry.",
        "date": "2026-10-10",
    },
    "roles": [
        {
            "label": "Sorting",
            "shifts": [
                {"startTime": "09:00", "endTime": "11:00"},
                {"startTime": "11:00", "endTime": "13:00"},
            ],
        },
        {
            "label": "Loading",
            "shifts": [
                {"startTime": "13:00", "endTime": "14:30"},
                {"startTime": "14:30", "endTime": "16:00"},
            ],
        },
    ],
}

HERITAGE_DAY = {
    "event": {
        "eventId": "k7m2xq9p",
        "createdAt": "2026-09-18T14:05:00.000Z",
        "name": "Heritage Day",
        "description": "Heritage Day is a celebration of Moravian tradition, community, and service.",
        "date": "2026-09-24",
    },
    "roles": [
        {
            "label": "Trash pickup",
            "shifts": [
                {"startTime": "08:00", "endTime": "10:00"},
                {"startTime": "10:00", "endTime": "12:00"},
                {"startTime": "12:00", "endTime": "14:00"},
                {"startTime": "14:00", "endTime": "16:00"},
            ],
        },
    ],
}


def pytest_sessionstart(session):
    """Fail fast if the running app is not healthy."""
    health_url = f"{BASE_URL}/health"
    try:
        with urllib.request.urlopen(health_url, timeout=1.0) as response:
            if response.status != 200:
                pytest.exit(
                    f"{health_url} returned {response.status} (expected 200). "
                    "Is DynamoDB Local running? Are the tables created? "
                    "Is the app running (python -m volunteer_signup.app)?",
                    returncode=1,
                )
    except (urllib.error.URLError, OSError) as exc:
        pytest.exit(
            f"App not reachable at {BASE_URL}. "
            "Start DynamoDB Local, create the tables, and run "
            "python -m volunteer_signup.app (see docs/development.md).\n"
            f"Details: {exc}",
            returncode=1,
        )


def _clear_tables(database: Database) -> None:
    tables = (
        (database.events, ("eventId",)),
        (database.roles, ("eventId", "roleId")),
        (database.shifts, ("roleKey", "shiftNumber")),
    )
    for table, key_names in tables:
        while True:
            page = table.scan()
            items = page.get("Items", [])
            if not items:
                break
            with table.batch_writer() as writer:
                for item in items:
                    writer.delete_item(Key={name: item[name] for name in key_names})


@pytest.fixture(scope="session")
def base_url():
    """URL of the already-running Flask app (pytest-playwright uses this)."""
    return BASE_URL


@pytest.fixture
def event_db():
    """Empty Database connected with ensure_settings (for arranging data)."""
    database = Database.from_env()
    _clear_tables(database)
    return database


@pytest.fixture
def food_drive(event_db):
    """One sample event with open shifts."""
    event_db.create_event(FOOD_DRIVE["event"], FOOD_DRIVE["roles"])
    return FOOD_DRIVE["event"]


@pytest.fixture
def heritage_day(event_db):
    """One sample event with an open shift and a taken shift."""
    event_db.create_event(HERITAGE_DAY["event"], HERITAGE_DAY["roles"])
    event_db.sign_up("k7m2xq9p", 1, 1, "Jack", "2026-09-19T16:20:00.000Z")
    return HERITAGE_DAY["event"]


@pytest.fixture
def two_events_newest_first(event_db):
    """Heritage Day (older) then Food Drive (newer) for browse-order checks."""
    event_db.create_event(HERITAGE_DAY["event"], HERITAGE_DAY["roles"])
    event_db.create_event(FOOD_DRIVE["event"], FOOD_DRIVE["roles"])
    return (FOOD_DRIVE["event"], HERITAGE_DAY["event"])
