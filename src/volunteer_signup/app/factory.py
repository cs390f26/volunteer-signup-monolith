from flask import Flask

from volunteer_signup.app.routes import register_routes


def create_app() -> Flask:
    """Create the Flask application and register its routes."""
    app = Flask("volunteer_signup")
    register_routes(app)
    return app


def launch() -> Flask:
    """Create the application for local development and deployment."""
    return create_app()
