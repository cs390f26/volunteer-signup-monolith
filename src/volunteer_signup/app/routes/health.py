from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    if current_app.extensions["volunteer_signup_db"].ping():
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "unavailable"}), 503
