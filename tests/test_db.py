import json
import runpy
from pathlib import Path

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from volunteer_signup.db import (
    DatabaseError,
    EventIdTakenError,
    NotFoundError,
    ShiftTakenError,
    read_seed_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = REPO_ROOT / "specs" / "sample-data.json"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed.py"
SIGNED_UP_AT = "2026-10-10T19:00:00.000Z"


def make_event(event_id="new00001"):
    return {
        "eventId": event_id,
        "createdAt": "2026-10-10T12:00:00.000Z",
        "name": "Community Cleanup",
        "description": "Help clean the neighborhood.",
        "date": "2026-11-01",
    }


def make_roles(role_count=1, shift_count=1):
    return [
        {
            "label": f"Role {number}",
            "shifts": [{"startTime": "09:00", "endTime": "10:00"}] * shift_count,
        }
        for number in range(1, role_count + 1)
    ]


def transaction_conflict():
    return ClientError(
        {
            "Error": {"Code": "TransactionCanceledException", "Message": "conflict"},
            "CancellationReasons": [{"Code": "TransactionConflict"}, {"Code": "None"}],
        },
        "TransactWriteItems",
    )


# Tables


def test_create_tables_uses_spec_key_schemas(db):
    expected = {
        "Events": [("eventId", "HASH")],
        "Roles": [("eventId", "HASH"), ("roleId", "RANGE")],
        "Shifts": [("roleKey", "HASH"), ("shiftNumber", "RANGE")],
    }
    for name, keys in expected.items():
        table = db.client.describe_table(TableName=name)["Table"]
        assert [(k["AttributeName"], k["KeyType"]) for k in table["KeySchema"]] == keys
        assert table["BillingModeSummary"]["BillingMode"] == "PAY_PER_REQUEST"


def test_create_tables_is_safe_to_rerun(seeded_db):
    seeded_db.create_tables()

    assert len(seeded_db.list_events()) == 3


def test_delete_tables_removes_all_tables(db):
    db.delete_tables()

    assert db.client.list_tables()["TableNames"] == []


def test_ping_reflects_table_availability(db):
    assert db.ping() is True

    db.delete_tables()

    assert db.ping() is False


def test_ping_is_false_when_endpoint_is_unreachable(db, monkeypatch):
    def unreachable(**kwargs):
        raise EndpointConnectionError(endpoint_url="http://localhost:8000")

    monkeypatch.setattr(db.client, "describe_table", unreachable)

    assert db.ping() is False


# Seed and reset


def test_seed_data_loads_every_item(seeded_db):
    roles = [
        role
        for event in seeded_db.list_events()
        for role in seeded_db.list_roles(event["eventId"])
    ]
    shifts = [
        shift
        for role in roles
        for shift in seeded_db.list_shifts(role["eventId"], int(role["roleId"]))
    ]

    assert len(seeded_db.list_events()) == 3
    assert len(roles) == 5
    assert len(shifts) == 11


def test_seed_script_loads_sample_data(db):
    runpy.run_path(str(SEED_SCRIPT))["main"]([])

    assert sorted(e["eventId"] for e in db.list_events()) == [
        "k7m2xq9p",
        "m3n8kp2w",
        "n4w8rt3c",
    ]


def test_seed_script_reset_replaces_existing_data(db):
    db.events.put_item(Item=make_event("extra001"))
    seed = runpy.run_path(str(SEED_SCRIPT))
    seed["LOCAL_HOSTS"].add("dynamodb.us-east-1.amazonaws.com")

    seed["main"](["--reset"])

    assert db.get_event("extra001") is None
    assert len(db.list_events()) == 3


def test_seed_script_refuses_reset_on_non_local_endpoint(db):
    db.events.put_item(Item=make_event("extra001"))

    with pytest.raises(SystemExit):
        runpy.run_path(str(SEED_SCRIPT))["main"](["--reset"])

    assert db.get_event("extra001") is not None


def test_seed_script_loads_a_custom_file(db, tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps({"events": [make_event("file0001")]}))

    runpy.run_path(str(SEED_SCRIPT))["main"](["--file", str(data_file)])

    assert db.get_event("file0001") is not None


# Reads


def test_list_events_follows_scan_pages(seeded_db):
    events = seeded_db.list_events(page_size=1)

    assert sorted(e["eventId"] for e in events) == ["k7m2xq9p", "m3n8kp2w", "n4w8rt3c"]


def test_list_roles_returns_creation_order(seeded_db):
    roles = seeded_db.list_roles("k7m2xq9p")

    assert [(r["roleId"], r["label"]) for r in roles] == [
        ("01", "Trash pickup"),
        ("02", "Greeter"),
    ]


def test_list_shifts_returns_creation_order_with_int_numbers(seeded_db):
    shifts = seeded_db.list_shifts("k7m2xq9p", 1)

    assert [s["shiftNumber"] for s in shifts] == [1, 2, 3, 4]
    assert all(type(s["shiftNumber"]) is int for s in shifts)
    assert shifts[0]["volunteerName"] == "Jack"
    assert "volunteerName" not in shifts[1]


def test_get_returns_items(seeded_db):
    assert seeded_db.get_event("k7m2xq9p")["name"] == "Heritage Day"
    assert seeded_db.get_role("k7m2xq9p", 2)["remainingShifts"] == 0
    assert seeded_db.get_shift("k7m2xq9p", 1, 3)["volunteerName"] == "Riley"


def test_get_returns_none_for_missing_items(seeded_db):
    assert seeded_db.get_event("zzzzzzzz") is None
    assert seeded_db.get_role("k7m2xq9p", 9) is None
    assert seeded_db.get_shift("k7m2xq9p", 1, 99) is None
    assert seeded_db.list_roles("zzzzzzzz") == []
    assert seeded_db.list_shifts("zzzzzzzz", 1) == []


def test_reads_raise_database_error_when_tables_are_missing(db):
    db.delete_tables()

    with pytest.raises(DatabaseError):
        db.list_events()


# create_event


def test_create_event_stores_event_roles_and_shifts(db):
    roles = [
        {"label": "Setup", "shifts": [{"startTime": "09:00", "endTime": "10:00"}]},
        {
            "label": "Cleanup",
            "shifts": [
                {"startTime": "13:00", "endTime": "14:30"},
                {"startTime": "14:30", "endTime": "16:00"},
            ],
        },
    ]

    db.create_event(make_event(), roles)

    assert db.get_event("new00001") == make_event()
    assert db.list_roles("new00001") == [
        {"eventId": "new00001", "roleId": "01", "label": "Setup", "shiftCount": 1, "remainingShifts": 1},
        {"eventId": "new00001", "roleId": "02", "label": "Cleanup", "shiftCount": 2, "remainingShifts": 2},
    ]
    assert db.list_shifts("new00001", 2) == [
        {"roleKey": "new00001#02", "shiftNumber": 1, "startTime": "13:00", "endTime": "14:30"},
        {"roleKey": "new00001#02", "shiftNumber": 2, "startTime": "14:30", "endTime": "16:00"},
    ]


def test_create_event_handles_maximum_size(db):
    db.create_event(make_event(), make_roles(role_count=10, shift_count=50))

    roles = db.list_roles("new00001")
    assert [r["roleId"] for r in roles] == [f"{n:02d}" for n in range(1, 11)]
    assert sum(len(db.list_shifts("new00001", n)) for n in range(1, 11)) == 500


def test_create_event_rejects_existing_id_without_touching_it(seeded_db):
    with pytest.raises(EventIdTakenError):
        seeded_db.create_event(make_event("k7m2xq9p"), make_roles())

    assert seeded_db.get_event("k7m2xq9p")["name"] == "Heritage Day"
    assert [r["label"] for r in seeded_db.list_roles("k7m2xq9p")] == ["Trash pickup", "Greeter"]


def test_create_event_rejects_id_used_by_leftover_roles(db):
    db.roles.put_item(
        Item={"eventId": "orphan01", "roleId": "01", "label": "Left", "shiftCount": 1, "remainingShifts": 1}
    )

    with pytest.raises(EventIdTakenError):
        db.create_event(make_event("orphan01"), make_roles())


def test_create_event_conditional_put_catches_a_race(seeded_db, monkeypatch):
    monkeypatch.setattr(seeded_db, "_event_id_in_use", lambda event_id: False)

    with pytest.raises(EventIdTakenError):
        seeded_db.create_event(make_event("k7m2xq9p"), make_roles())


# sign_up


def test_sign_up_records_name_and_decrements_remaining(seeded_db):
    shift = seeded_db.sign_up("k7m2xq9p", 1, 2, "Alex", SIGNED_UP_AT)

    assert shift == {
        "roleKey": "k7m2xq9p#01",
        "shiftNumber": 2,
        "startTime": "10:00",
        "endTime": "12:00",
        "volunteerName": "Alex",
        "signedUpAt": SIGNED_UP_AT,
    }
    assert seeded_db.get_role("k7m2xq9p", 1)["remainingShifts"] == 1


def test_sign_up_rejects_taken_shift_without_changes(seeded_db):
    with pytest.raises(ShiftTakenError):
        seeded_db.sign_up("k7m2xq9p", 1, 1, "Sam", SIGNED_UP_AT)

    assert seeded_db.get_shift("k7m2xq9p", 1, 1)["volunteerName"] == "Jack"
    assert seeded_db.get_role("k7m2xq9p", 1)["remainingShifts"] == 2


def test_second_signup_for_same_shift_is_rejected(seeded_db):
    seeded_db.sign_up("n4w8rt3c", 1, 1, "First", SIGNED_UP_AT)

    with pytest.raises(ShiftTakenError):
        seeded_db.sign_up("n4w8rt3c", 1, 1, "Second", SIGNED_UP_AT)

    assert seeded_db.get_shift("n4w8rt3c", 1, 1)["volunteerName"] == "First"
    assert seeded_db.get_role("n4w8rt3c", 1)["remainingShifts"] == 0


def test_sign_up_for_missing_shift_creates_nothing(seeded_db):
    with pytest.raises(NotFoundError):
        seeded_db.sign_up("k7m2xq9p", 1, 99, "Sam", SIGNED_UP_AT)

    assert seeded_db.get_shift("k7m2xq9p", 1, 99) is None
    assert seeded_db.get_role("k7m2xq9p", 1)["remainingShifts"] == 2


@pytest.mark.parametrize(
    ("event_id", "role_number"),
    [("k7m2xq9p", 9), ("zzzzzzzz", 1)],
)
def test_sign_up_for_missing_role_or_event_is_not_found(seeded_db, event_id, role_number):
    with pytest.raises(NotFoundError):
        seeded_db.sign_up(event_id, role_number, 1, "Sam", SIGNED_UP_AT)


def test_sign_up_with_inconsistent_counter_is_database_error(seeded_db):
    seeded_db.roles.update_item(
        Key={"eventId": "m3n8kp2w", "roleId": "01"},
        UpdateExpression="SET remainingShifts = :zero",
        ExpressionAttributeValues={":zero": 0},
    )

    with pytest.raises(DatabaseError):
        seeded_db.sign_up("m3n8kp2w", 1, 1, "Sam", SIGNED_UP_AT)

    assert "volunteerName" not in seeded_db.get_shift("m3n8kp2w", 1, 1)


def test_sign_up_retries_after_transaction_conflict(seeded_db, monkeypatch):
    real_transact = seeded_db.client.transact_write_items
    calls = []

    def conflict_once(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise transaction_conflict()
        return real_transact(**kwargs)

    monkeypatch.setattr(seeded_db.client, "transact_write_items", conflict_once)

    shift = seeded_db.sign_up("m3n8kp2w", 2, 1, "Lee", SIGNED_UP_AT)

    assert shift["volunteerName"] == "Lee"
    assert len(calls) == 2


def test_sign_up_gives_up_after_repeated_conflicts(seeded_db, monkeypatch):
    calls = []

    def always_conflict(**kwargs):
        calls.append(kwargs)
        raise transaction_conflict()

    monkeypatch.setattr(seeded_db.client, "transact_write_items", always_conflict)

    with pytest.raises(DatabaseError):
        seeded_db.sign_up("m3n8kp2w", 2, 1, "Lee", SIGNED_UP_AT)

    assert len(calls) == 4
    assert "volunteerName" not in seeded_db.get_shift("m3n8kp2w", 2, 1)


def test_sample_data_counters_match_open_shifts():
    data = read_seed_file(SAMPLE_DATA)

    for role in data["roles"]:
        key = f"{role['eventId']}#{role['roleId']}"
        shifts = [s for s in data["shifts"] if s["roleKey"] == key]
        assert len(shifts) == role["shiftCount"]
        assert sum("volunteerName" not in s for s in shifts) == role["remainingShifts"]
