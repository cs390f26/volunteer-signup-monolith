from pathlib import Path

import pytest
from moto import mock_aws

from volunteer_signup.db import Database, read_seed_file

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = REPO_ROOT / "specs" / "sample-data.json"

# moto only intercepts AWS-style endpoints, so tests never point at DynamoDB Local.
TEST_SETTINGS = {
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_DEFAULT_REGION": "us-east-1",
    "EVENTS_TABLE_NAME": "Events",
    "ROLES_TABLE_NAME": "Roles",
    "SHIFTS_TABLE_NAME": "Shifts",
    "DYNAMODB_ENDPOINT_URL": "https://dynamodb.us-east-1.amazonaws.com",
}


@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    """Keep every test on fake credentials, whatever is in .env."""
    for name, value in TEST_SETTINGS.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def db():
    """A Database backed by moto, with empty tables."""
    with mock_aws():
        database = Database(TEST_SETTINGS)
        database.create_tables()
        yield database


@pytest.fixture
def seeded_db(db):
    """A Database loaded with specs/sample-data.json."""
    db.load_items(read_seed_file(SAMPLE_DATA))
    return db
