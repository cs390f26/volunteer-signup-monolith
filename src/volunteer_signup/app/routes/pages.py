from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def event_page():
    return render_template("event.html")


@pages_bp.get("/create")
def create_page():
    return render_template("create.html")


@pages_bp.get("/role")
def role_page():
    return render_template("role.html")


@pages_bp.get("/confirm")
def confirm_page():
    return render_template("confirm.html")
