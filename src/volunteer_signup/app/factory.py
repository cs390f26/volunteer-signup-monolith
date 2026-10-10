from flask import Flask

from volunteer_signup.app.routes import register_routes


def create_app(service: object | None = None) -> Flask:
    """Create the Flask application and register its routes."""
    app = Flask("volunteer_signup")
    app.extensions["volunteer_signup_service"] = service
    register_routes(app)
    return app


def launch() -> Flask:
    """Create the application for local development and deployment."""
    return create_app()
