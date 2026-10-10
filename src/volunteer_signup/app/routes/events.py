from flask import Blueprint, current_app, jsonify, request

from volunteer_signup.service.errors import (
    ServiceUnavailableError,
    ValidationError,
)

events_bp = Blueprint("events", __name__)


@events_bp.get("/events")
@events_bp.get("/events")
def list_events():
    service = current_app.extensions["volunteer_signup_service"]

    try:
        events = service.list_events()
    except ServiceUnavailableError:
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to complete the request",
                }
            }
        ), 500

    return jsonify({"events": events}), 200

@events_bp.post("/events")
def create_event():
    service = current_app.extensions["volunteer_signup_service"]
    event_data = request.get_json(silent=True)

    if not isinstance(event_data, dict):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "JSON body required"}}), 400

    try:
        event_id = service.create_event(event_data)
    
    except ValidationError as exc:
        return jsonify(
            {
                "error": {
                    "code": "BAD_REQUEST", 
                    "message": str(exc)
                }
            }
        ), 400

    except ServiceUnavailableError:
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to complete the request",
                }
            }
        ), 500

    return jsonify({"id": event_id}), 201