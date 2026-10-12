import re

from volunteer_signup.app import create_app


def test_complete_event_and_signup_flow_uses_database(db):
    app = create_app(db=db)
    client = app.test_client()

    create_response = client.post(
        "/events",
        json={
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
        },
    )

    assert create_response.status_code == 201
    event_id = create_response.get_json()["id"]
    assert re.fullmatch(r"[a-z0-9]{8}", event_id)

    list_response = client.get("/events")

    assert list_response.status_code == 200
    assert list_response.get_json() == {
        "events": [
            {
                "id": event_id,
                "name": "Community Cleanup",
                "description": "Help clean the neighborhood.",
                "date": "2026-10-20",
                "roles": [
                    {
                        "number": 1,
                        "label": "Setup Crew",
                        "totalShifts": 1,
                        "openShifts": 1,
                    }
                ],
            }
        ]
    }

    role_response = client.get(f"/events/{event_id}/roles/1")

    assert role_response.status_code == 200
    assert role_response.get_json()["shifts"][0]["available"] is True

    signup_response = client.post(
        f"/events/{event_id}/roles/1/shifts/1/signup",
        json={"name": "Alex Morgan"},
    )

    assert signup_response.status_code == 200
    assert signup_response.get_json()["volunteerName"] == "Alex Morgan"
    assert signup_response.get_json()["available"] is False

    updated_role_response = client.get(f"/events/{event_id}/roles/1")

    updated_shift = updated_role_response.get_json()["shifts"][0]
    assert updated_shift["available"] is False
    assert updated_shift["volunteerName"] == "Alex Morgan"

    conflict_response = client.post(
        f"/events/{event_id}/roles/1/shifts/1/signup",
        json={"name": "Second Volunteer"},
    )

    assert conflict_response.status_code == 409
    assert conflict_response.get_json() == {
        "error": {
            "code": "SHIFT_TAKEN",
            "message": "Shift is no longer available",
        }
    }

    final_role_response = client.get(f"/events/{event_id}/roles/1")

    final_shift = final_role_response.get_json()["shifts"][0]
    assert final_shift["volunteerName"] == "Alex Morgan"


def test_empty_database_returns_empty_event_list(db):
    app = create_app(db=db)
    client = app.test_client()

    response = client.get("/events")

    assert response.status_code == 200
    assert response.get_json() == {"events": []}
