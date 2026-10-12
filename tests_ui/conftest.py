"""Shared setup for Playwright acceptance tests.

Assumes DynamoDB Local and Flask are already running on the usual ports
(see docs/development.md). This file only checks that the app is healthy, exposes
base_url for pytest-playwright, and provides data fixtures via Database.
"""

import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests_ui.sample_events import FOOD_DRIVE_ID, HERITAGE_DAY_ID
from volunteer_signup.config import ensure_settings
from volunteer_signup.db import Database, read_seed_file

# Same host/port as python -m volunteer_signup.app (app.run(port=5000)).
BASE_URL = "http://127.0.0.1:5000"
SAMPLE_DATA = Path(__file__).resolve().parent.parent / "specs" / "sample-data.json"


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
    """Remove every item so each test starts from a known empty store."""
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
    ensure_settings()
    database = Database.from_env()
    _clear_tables(database)
    return database


@pytest.fixture
def sample_events(event_db):
    """Sample events from specs/sample-data.json in an otherwise empty store."""
    event_db.load_items(read_seed_file(SAMPLE_DATA))
    return read_seed_file(SAMPLE_DATA)


@pytest.fixture
def heritage_day(sample_events):
    """Heritage Day, which has both open and taken shifts."""
    return next(
        event
        for event in sample_events["events"]
        if event["eventId"] == HERITAGE_DAY_ID
    )


@pytest.fixture
def food_drive(sample_events):
    """Food Drive Sorting, the newest sample event."""
    return next(
        event
        for event in sample_events["events"]
        if event["eventId"] == FOOD_DRIVE_ID
    )


@pytest.fixture
def two_events_newest_first(event_db):
    """Two events for browse-order checks; the second create is the newer one."""
    older = {
        "eventId": "olderev1",
        "createdAt": "2026-09-01T10:00:00.000Z",
        "name": "Older Cleanup",
        "description": "The earlier event.",
        "date": "2026-09-15",
    }
    newer = {
        "eventId": "newerev1",
        "createdAt": "2026-09-20T10:00:00.000Z",
        "name": "Newer Cleanup",
        "description": "The later event.",
        "date": "2026-10-01",
    }
    roles = [
        {
            "label": "Helper",
            "shifts": [{"startTime": "09:00", "endTime": "10:00"}],
        }
    ]
    event_db.create_event(older, roles)
    event_db.create_event(newer, roles)
    return (newer, older)
