import pytest

from volunteer_signup.app import create_app
from volunteer_signup.db.errors import (
    DatabaseError,
    EventIdTakenError,
    ShiftTakenError,
)
from volunteer_signup.db.errors import (
    NotFoundError as DatabaseNotFoundError,
)
from volunteer_signup.service.errors import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from volunteer_signup.service.service import VolunteerSignupService


class FakeDatabase:
    def list_events(self):
        return [
            {
                "eventId": "older001",
                "createdAt": "2026-10-10T10:00:00.000Z",
                "name": "Older Event",
                "description": "The older event.",
                "date": "2026-10-20",
            },
            {
                "eventId": "newer001",
                "createdAt": "2026-10-11T10:00:00.000Z",
                "name": "Newer Event",
                "description": "The newer event.",
                "date": "2026-10-21",
            },
        ]

    def list_roles(self, event_id):
        return [
            {
                "eventId": event_id,
                "roleId": "01",
                "label": "Setup Crew",
                "shiftCount": 3,
                "remainingShifts": 2,
            }
        ]


def test_list_events_maps_database_items_and_sorts_newest_first():
    service = VolunteerSignupService(FakeDatabase())

    events = service.list_events()

    assert events == [
        {
            "id": "newer001",
            "name": "Newer Event",
            "description": "The newer event.",
            "date": "2026-10-21",
            "roles": [
                {
                    "number": 1,
                    "label": "Setup Crew",
                    "totalShifts": 3,
                    "openShifts": 2,
                }
            ],
        },
        {
            "id": "older001",
            "name": "Older Event",
            "description": "The older event.",
            "date": "2026-10-20",
            "roles": [
                {
                    "number": 1,
                    "label": "Setup Crew",
                    "totalShifts": 3,
                    "openShifts": 2,
                }
            ],
        },
    ]


class FailingListDatabase:
    def list_events(self):
        raise DatabaseError("database unavailable")


def test_list_events_translates_database_error():
    service = VolunteerSignupService(FailingListDatabase())

    with pytest.raises(ServiceUnavailableError):
        service.list_events()


class CreateDatabase:
    def __init__(self):
        self.event = None
        self.roles = None

    def create_event(self, event, roles):
        self.event = event
        self.roles = roles


def test_create_event_stores_api_data_and_returns_generated_id():
    db = CreateDatabase()
    service = VolunteerSignupService(
        db,
        id_generator=lambda: "new00001",
        clock=lambda: "2026-10-11T16:30:00.000Z",
    )
    event_data = {
        "name": "Community Cleanup",
        "description": "Help clean the neighborhood.",
        "date": "2026-10-20",
        "roles": [
            {
                "label": "Setup Crew",
                "shifts": [
                    {
                        "startTime": "09:00",
                        "endTime": "10:30",
                    }
                ],
            }
        ],
    }

    event_id = service.create_event(event_data)

    assert event_id == "new00001"
    assert db.event == {
        "eventId": "new00001",
        "createdAt": "2026-10-11T16:30:00.000Z",
        "name": "Community Cleanup",
        "description": "Help clean the neighborhood.",
        "date": "2026-10-20",
    }
    assert db.roles == event_data["roles"]


def test_create_event_rejects_blank_name():
    db = CreateDatabase()
    service = VolunteerSignupService(db)

    with pytest.raises(ValidationError, match="name"):
        service.create_event(
            {
                "name": "   ",
                "description": "Help clean the neighborhood.",
                "date": "2026-10-20",
                "roles": [
                    {
                        "label": "Setup Crew",
                        "shifts": [
                            {
                                "startTime": "09:00",
                                "endTime": "10:00",
                            }
                        ],
                    }
                ],
            }
        )

    assert db.event is None


def test_create_event_rejects_invalid_date():
    db = CreateDatabase()
    service = VolunteerSignupService(db)

    with pytest.raises(ValidationError, match="date"):
        service.create_event(
            {
                "name": "Community Cleanup",
                "description": "Help clean the neighborhood.",
                "date": "2026-02-30",
                "roles": [
                    {
                        "label": "Setup Crew",
                        "shifts": [
                            {
                                "startTime": "09:00",
                                "endTime": "10:00",
                            }
                        ],
                    }
                ],
            }
        )

    assert db.event is None


def test_create_event_requires_at_least_one_role():
    db = CreateDatabase()
    service = VolunteerSignupService(db)

    with pytest.raises(ValidationError, match="roles"):
        service.create_event(
            {
                "name": "Community Cleanup",
                "description": "Help clean the neighborhood.",
                "date": "2026-10-20",
                "roles": [],
            }
        )

    assert db.event is None


@pytest.mark.parametrize(
    "roles",
    [
        [
            {
                "label": "   ",
                "shifts": [{"startTime": "09:00", "endTime": "10:00"}],
            }
        ],
        [
            {
                "label": "Setup Crew",
                "shifts": [{"startTime": "09:00", "endTime": "10:00"}],
            },
            {
                "label": " Setup Crew ",
                "shifts": [{"startTime": "10:00", "endTime": "11:00"}],
            },
        ],
    ],
)
def test_create_event_rejects_invalid_or_duplicate_role_labels(roles):
    db = CreateDatabase()
    service = VolunteerSignupService(db)

    with pytest.raises(ValidationError, match="role"):
        service.create_event(
            {
                "name": "Community Cleanup",
                "description": "Help clean the neighborhood.",
                "date": "2026-10-20",
                "roles": roles,
            }
        )

    assert db.event is None


@pytest.mark.parametrize(
    "shifts",
    [
        [],
        [{"startTime": "10:00", "endTime": "09:00"}],
        [{"startTime": "9 AM", "endTime": "10 AM"}],
    ],
)
def test_create_event_rejects_invalid_shifts(shifts):
    db = CreateDatabase()
    service = VolunteerSignupService(db)

    with pytest.raises(ValidationError, match="shift"):
        service.create_event(
            {
                "name": "Community Cleanup",
                "description": "Help clean the neighborhood.",
                "date": "2026-10-20",
                "roles": [
                    {
                        "label": "Setup Crew",
                        "shifts": shifts,
                    }
                ],
            }
        )

    assert db.event is None


class FailingCreateDatabase:
    def create_event(self, event, roles):
        raise DatabaseError("database unavailable")


def test_create_event_translates_database_error():
    service = VolunteerSignupService(
        FailingCreateDatabase(),
        id_generator=lambda: "new00001",
    )

    with pytest.raises(ServiceUnavailableError):
        service.create_event(
            {
                "name": "Community Cleanup",
                "description": "Help clean the neighborhood.",
                "date": "2026-10-20",
                "roles": [
                    {
                        "label": "Setup Crew",
                        "shifts": [
                            {
                                "startTime": "09:00",
                                "endTime": "10:00",
                            }
                        ],
                    }
                ],
            }
        )


class CollidingCreateDatabase:
    def __init__(self):
        self.event_ids = []

    def create_event(self, event, roles):
        self.event_ids.append(event["eventId"])

        if len(self.event_ids) == 1:
            raise EventIdTakenError(event["eventId"])


def test_create_event_retries_when_generated_id_is_taken():
    db = CollidingCreateDatabase()
    event_ids = iter(["taken001", "new00001"])
    service = VolunteerSignupService(
        db,
        id_generator=lambda: next(event_ids),
        clock=lambda: "2026-10-11T16:30:00.000Z",
    )

    event_id = service.create_event(
        {
            "name": "Community Cleanup",
            "description": "Help clean the neighborhood.",
            "date": "2026-10-20",
            "roles": [
                {
                    "label": "Setup Crew",
                    "shifts": [
                        {
                            "startTime": "09:00",
                            "endTime": "10:00",
                        }
                    ],
                }
            ],
        }
    )

    assert event_id == "new00001"
    assert db.event_ids == ["taken001", "new00001"]


class RoleDatabase:
    def get_event(self, event_id):
        return {
            "eventId": event_id,
            "name": "Community Cleanup",
            "date": "2026-10-20",
        }

    def get_role(self, event_id, role_number):
        return {
            "eventId": event_id,
            "roleId": f"{role_number:02d}",
            "label": "Setup Crew",
            "shiftCount": 2,
            "remainingShifts": 1,
        }

    def list_shifts(self, event_id, role_number):
        return [
            {
                "roleKey": f"{event_id}#01",
                "shiftNumber": 1,
                "startTime": "09:00",
                "endTime": "10:00",
            },
            {
                "roleKey": f"{event_id}#01",
                "shiftNumber": 2,
                "startTime": "10:00",
                "endTime": "11:30",
                "volunteerName": "Alex Morgan",
                "signedUpAt": "2026-10-11T16:30:00.000Z",
            },
        ]


def test_get_role_maps_event_role_and_shifts():
    service = VolunteerSignupService(RoleDatabase())

    role = service.get_role("event001", 1)

    assert role == {
        "eventId": "event001",
        "eventName": "Community Cleanup",
        "eventDate": "2026-10-20",
        "number": 1,
        "label": "Setup Crew",
        "shifts": [
            {
                "number": 1,
                "startTime": "09:00",
                "endTime": "10:00",
                "available": True,
            },
            {
                "number": 2,
                "startTime": "10:00",
                "endTime": "11:30",
                "available": False,
                "volunteerName": "Alex Morgan",
            },
        ],
    }


class MissingRoleDatabase:
    def get_event(self, event_id):
        return {
            "eventId": event_id,
            "name": "Community Cleanup",
            "date": "2026-10-20",
        }

    def get_role(self, event_id, role_number):
        return None

    def list_shifts(self, event_id, role_number):
        raise AssertionError("shifts should not be read for a missing role")


def test_get_role_raises_not_found_when_role_is_missing():
    service = VolunteerSignupService(MissingRoleDatabase())

    with pytest.raises(NotFoundError):
        service.get_role("event001", 9)


class SignupDatabase:
    def __init__(self):
        self.signup_args = None

    def sign_up(
        self,
        event_id,
        role_number,
        shift_number,
        name,
        signed_up_at,
    ):
        self.signup_args = (
            event_id,
            role_number,
            shift_number,
            name,
            signed_up_at,
        )

        return {
            "roleKey": f"{event_id}#{role_number:02d}",
            "shiftNumber": shift_number,
            "startTime": "09:00",
            "endTime": "10:30",
            "volunteerName": name,
            "signedUpAt": signed_up_at,
        }


def test_signup_for_shift_records_and_maps_signup():
    db = SignupDatabase()
    service = VolunteerSignupService(
        db,
        clock=lambda: "2026-10-11T16:30:00.000Z",
    )

    shift = service.signup_for_shift(
        "event001",
        1,
        2,
        " Alex Morgan ",
    )

    assert db.signup_args == (
        "event001",
        1,
        2,
        "Alex Morgan",
        "2026-10-11T16:30:00.000Z",
    )
    assert shift == {
        "number": 2,
        "startTime": "09:00",
        "endTime": "10:30",
        "available": False,
        "volunteerName": "Alex Morgan",
    }


class FailingSignupDatabase:
    def __init__(self, error):
        self.error = error

    def sign_up(
        self,
        event_id,
        role_number,
        shift_number,
        name,
        signed_up_at,
    ):
        raise self.error


@pytest.mark.parametrize(
    ("database_error", "service_error"),
    [
        (DatabaseNotFoundError(), NotFoundError),
        (ShiftTakenError(), ConflictError),
        (DatabaseError("database unavailable"), ServiceUnavailableError),
    ],
)
def test_signup_for_shift_translates_database_errors(
    database_error,
    service_error,
):
    service = VolunteerSignupService(FailingSignupDatabase(database_error))

    with pytest.raises(service_error):
        service.signup_for_shift(
            "event001",
            1,
            1,
            "Alex Morgan",
        )


def test_create_app_builds_real_service_from_database(db):
    app = create_app(db=db)

    service = app.extensions["volunteer_signup_service"]

    assert isinstance(service, VolunteerSignupService)
    assert service.db is db
