from flask import Blueprint, current_app, jsonify

from volunteer_signup.service.errors import (
    NotFoundError,
    ServiceUnavailableError,
)

roles_bp = Blueprint("roles", __name__)


@roles_bp.get("/events/<event_id>/roles/<int:role_number>")
def get_role(event_id, role_number):
    service = current_app.extensions["volunteer_signup_service"]

    try:
        role = service.get_role(event_id, role_number)
    except NotFoundError:
        return jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Requested resource not found",
                }
            }
        ), 404

    except ServiceUnavailableError:
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to complete the request",
                }
            }
        ), 500

    return jsonify(role), 200