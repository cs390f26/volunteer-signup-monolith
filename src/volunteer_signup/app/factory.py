from pathlib import Path

from flask import Flask, jsonify

from volunteer_signup.app.routes import register_routes
from volunteer_signup.db import Database
from volunteer_signup.service import VolunteerSignupService

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def create_app(
    service: object | None = None,
    db: Database | None = None,
) -> Flask:
    """Create the Flask application and register its routes."""
    app = Flask(
        "volunteer_signup",
        template_folder=str(PACKAGE_ROOT / "templates"),
        static_folder=str(PACKAGE_ROOT / "static"),
    )
    database = db if db is not None else Database.from_env()
    application_service = (
        service if service is not None else VolunteerSignupService(database)
    )

    app.extensions["volunteer_signup_db"] = database
    app.extensions["volunteer_signup_service"] = application_service
    register_routes(app)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Requested resource not found",
                }
            }
        ), 404

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to complete the request",
                }
            }
        ), 500

    return app


def launch() -> Flask:
    """Create the application for local development and deployment."""
    return create_app()
