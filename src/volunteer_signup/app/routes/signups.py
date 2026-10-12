from flask import Blueprint, current_app, jsonify, request

from volunteer_signup.service.errors import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)

signups_bp = Blueprint("signups", __name__)


@signups_bp.post(
    "/events/<event_id>/roles/<int:role_number>/shifts/<int:shift_number>/signup"
)
def signup_for_shift(event_id, role_number, shift_number):
    service = current_app.extensions["volunteer_signup_service"]
    signup_data = request.get_json(silent=True)

    if not isinstance(signup_data, dict):
        return jsonify(
            {
                "error": {
                    "code": "BAD_REQUEST",
                    "message": "JSON body required",
                }
            }
        ), 400

    volunteer_name = signup_data.get("name")

    try:
        shift = service.signup_for_shift(
            event_id,
            role_number,
            shift_number,
            volunteer_name,
        )

    except NotFoundError:
        return jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Requested resource not found",
                }
            }
        ), 404

    except ConflictError:
        return jsonify(
            {
                "error": {
                    "code": "SHIFT_TAKEN",
                    "message": "Shift is no longer available",
                }
            }
        ), 409

    except ServiceUnavailableError:
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to complete the request",
                }
            }
        ), 500

    except ValidationError as error:
        return jsonify(
            {
                "error": {
                    "code": "BAD_REQUEST",
                    "message": str(error),
                }
            }
        ), 400

    return jsonify(shift), 200
