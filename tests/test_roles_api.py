from volunteer_signup.app import create_app
from volunteer_signup.service.errors import (
    NotFoundError,
    ServiceUnavailableError,
)


class FakeRoleService:
    def __init__(self, role):
        self.role = role
        self.requested_role = None

    def get_role(self, event_id, role_number):
        self.requested_role = (event_id, role_number)
        return self.role


def test_get_role_returns_role_details():
    role = {
        "eventId": "evt12345",
        "eventName": "Community Garden Day",
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
                "endTime": "11:00",
                "available": False,
                "volunteerName": "Alex Morgan",
            },
        ],
    }

    service = FakeRoleService(role)
    app = create_app(service=service)
    client = app.test_client()

    response = client.get("/events/evt12345/roles/1")

    assert response.status_code == 200
    assert response.get_json() == role
    assert service.requested_role == ("evt12345", 1)

class MissingRoleService:
    def get_role(self, event_id, role_number):
        raise NotFoundError("role not found")


def test_get_role_returns_not_found_for_unknown_role():
    app = create_app(service=MissingRoleService())
    client = app.test_client()

    response = client.get("/events/missing/roles/1")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Requested resource not found",
        }
    }

class FailingRoleService:
    def get_role(self, event_id, role_number):
        raise ServiceUnavailableError("database unavailable")


def test_get_role_returns_internal_error_when_service_fails():
    app = create_app(service=FailingRoleService())
    client = app.test_client()

    response = client.get("/events/evt12345/roles/1")

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unable to complete the request",
        }
    }