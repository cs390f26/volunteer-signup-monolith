"""Route blueprints, one module per area of the API."""

from flask import Flask

from volunteer_signup.app.routes.events import events_bp
from volunteer_signup.app.routes.health import health_bp
from volunteer_signup.app.routes.roles import roles_bp
from volunteer_signup.app.routes.signups import signups_bp


def register_routes(app: Flask) -> None:
    """Register every blueprint on the application."""
    app.register_blueprint(health_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(signups_bp)