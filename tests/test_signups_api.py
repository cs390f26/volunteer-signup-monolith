from volunteer_signup.app import create_app
from volunteer_signup.service.errors import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


class FakeSignupService:
    def signup_for_shift(
        self,
        event_id,
        role_number,
        shift_number,
        volunteer_name,
    ):
        return {
            "number": shift_number,
            "startTime": "09:00",
            "endTime": "10:00",
            "available": False,
            "volunteerName": volunteer_name,
        }


def test_signup_for_shift_records_volunteer():
    app = create_app(service=FakeSignupService())
    client = app.test_client()

    response = client.post(
        "/events/evt12345/roles/1/shifts/1/signup",
        json={"name": "Alex Morgan"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "number": 1,
        "startTime": "09:00",
        "endTime": "10:00",
        "available": False,
        "volunteerName": "Alex Morgan",
    }

def test_signup_for_shift_requires_json_body():
    app = create_app(service=FakeSignupService())
    client = app.test_client()

    response = client.post(
        "/events/evt12345/roles/1/shifts/1/signup"
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "JSON body required",
        }
    }

def test_signup_for_shift_requires_volunteer_name():
    app = create_app(service=FakeSignupService())
    client = app.test_client()

    response = client.post(
        "/events/evt12345/roles/1/shifts/1/signup",
        json={},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "Volunteer name is required",
        }
    }

class MissingShiftService:
    def signup_for_shift(
        self,
        event_id,
        role_number,
        shift_number,
        volunteer_name,
    ):
        raise NotFoundError("shift not found")


def test_signup_for_shift_returns_not_found_for_unknown_shift():
    app = create_app(service=MissingShiftService())
    client = app.test_client()

    response = client.post(
        "/events/missing/roles/1/shifts/1/signup",
        json={"name": "Alex Morgan"},
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Requested resource not found",
        }
    }

class TakenShiftService:
    def signup_for_shift(
        self,
        event_id,
        role_number,
        shift_number,
        volunteer_name,
    ):
        raise ConflictError("shift already taken")


def test_signup_for_shift_returns_conflict_when_shift_is_taken():
    app = create_app(service=TakenShiftService())
    client = app.test_client()

    response = client.post(
        "/events/evt12345/roles/1/shifts/1/signup",
        json={"name": "Alex Morgan"},
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": {
            "code": "SHIFT_TAKEN",
            "message": "Shift is no longer available",
        }
    }

class FailingSignupService:
    def signup_for_shift(
        self,
        event_id,
        role_number,
        shift_number,
        volunteer_name,
    ):
        raise ServiceUnavailableError("database unavailable")


def test_signup_for_shift_returns_internal_error_when_service_fails():
    app = create_app(service=FailingSignupService())
    client = app.test_client()

    response = client.post(
        "/events/evt12345/roles/1/shifts/1/signup",
        json={"name": "Alex Morgan"},
    )

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unable to complete the request",
        }
    }

class InvalidSignupService:
    def signup_for_shift(
        self,
        event_id,
        role_number,
        shift_number,
        volunteer_name,
    ):
        raise ValidationError("name must be between 1 and 100 characters")


def test_signup_for_shift_returns_bad_request_for_invalid_name():
    app = create_app(service=InvalidSignupService())
    client = app.test_client()

    response = client.post(
        "/events/evt12345/roles/1/shifts/1/signup",
        json={"name": "A" * 101},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "name must be between 1 and 100 characters",
        }
    }