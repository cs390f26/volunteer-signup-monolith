from volunteer_signup.app import create_app
from volunteer_signup.service.errors import ServiceUnavailableError


class FakeService:
    """Temporary service used to test the API without DynamoDB."""

    def __init__(self, events=None):
        self.events = events or []

    def list_events(self):
        return self.events


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