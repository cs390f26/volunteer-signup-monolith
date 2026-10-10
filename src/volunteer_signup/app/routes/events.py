from flask import Blueprint, current_app, jsonify

from volunteer_signup.service.errors import ServiceUnavailableError

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