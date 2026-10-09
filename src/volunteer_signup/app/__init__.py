"""Flask application: the app factory and the API and web routes."""

from volunteer_signup.app.factory import create_app, launch

__all__ = ["create_app", "launch"]
