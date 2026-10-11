from flask import Flask

from volunteer_signup.app.routes import register_routes
from volunteer_signup.db import Database


def create_app(
    service: object | None = None,
    db: Database | None = None,
) -> Flask:
    """Create the Flask application and register its routes."""
    app = Flask("volunteer_signup")
    app.extensions["volunteer_signup_db"] = db if db is not None else Database.from_env()
    app.extensions["volunteer_signup_service"] = service
    register_routes(app)
    return app


def launch() -> Flask:
    """Create the application for local development and deployment."""
    return create_app()
