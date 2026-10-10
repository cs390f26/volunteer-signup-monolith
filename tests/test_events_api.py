from volunteer_signup.app import create_app
from volunteer_signup.service.errors import (
    ServiceUnavailableError,
    ValidationError,
)


class FakeService:
    """Temporary service used to test the API without DynamoDB."""

    def __init__(self, events=None):
        self.events = events or []
        self.created_event = None

    def list_events(self):
        return self.events

    def create_event(self, event_data):
        self.created_event = event_data
        return "evtnew01"


def test_list_events_returns_empty_list():
    app = create_app(service=FakeService())
    client = app.test_client()

    response = client.get("/events")

    assert response.status_code == 200
    assert response.get_json() == {"events": []}

def test_list_events_returns_event_summaries():
    events = [
        {
            "id": "evt12345",
            "name": "Community Garden Day",
            "description": "Help prepare the community garden.",
            "date": "2026-10-20",
            "roles": [
                {
                    "number": 1,
                    "label": "Setup Crew",
                    "totalShifts": 5,
                    "openShifts": 3,
                }
            ],
        }
    ]

    app = create_app(service=FakeService(events))
    client = app.test_client()

    response = client.get("/events")

    assert response.status_code == 200
    assert response.get_json() == {"events": events}

class FailingService:
    def list_events(self):
        raise ServiceUnavailableError("database unavailable")


def test_list_events_returns_internal_error_when_service_fails():
    app = create_app(service=FailingService())
    client = app.test_client()

    response = client.get("/events")

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unable to complete the request",
        }
    }

def test_create_event_returns_created_event_id():
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
                        "endTime": "10:00",
                    }
                ],
            }
        ],
    }

    service = FakeService()
    app = create_app(service=service)
    client = app.test_client()

    response = client.post("/events", json=event_data)

    assert response.status_code == 201
    assert response.get_json() == {"id": "evtnew01"}
    assert service.created_event == event_data

def test_create_event_rejects_missing_json_body():
    app = create_app(service=FakeService())
    client = app.test_client()

    response = client.post("/events")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "JSON body required",
        }
    }

class InvalidEventService:
    def create_event(self, event_data):
        raise ValidationError("name is required")


def test_create_event_returns_bad_request_for_invalid_data():
    app = create_app(service=InvalidEventService())
    client = app.test_client()

    response = client.post("/events", json={"name": ""})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "name is required",
        }
    }

class FailingCreateService:
    def create_event(self, event_data):
        raise ServiceUnavailableError("database unavailable")


def test_create_event_returns_internal_error_when_service_fails():
    app = create_app(service=FailingCreateService())
    client = app.test_client()

    response = client.post("/events", json={"name": "Community Cleanup"})

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unable to complete the request",
        }
    }