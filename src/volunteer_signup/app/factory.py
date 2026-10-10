from pathlib import Path

from flask import Flask

from volunteer_signup.app.routes import register_routes

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def create_app(service: object | None = None) -> Flask:
    """Create the Flask application and register its routes."""
    app = Flask(
        "volunteer_signup",
        template_folder=str(PACKAGE_ROOT / "templates"),
        static_folder=str(PACKAGE_ROOT / "static"),
    )
    app.extensions["volunteer_signup_service"] = service
    register_routes(app)
    return app


def launch() -> Flask:
    """Create the application for local development and deployment."""
    return create_app()
