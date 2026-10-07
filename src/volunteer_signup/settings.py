"""Load and validate the settings required by the application."""

import os

from dotenv import load_dotenv

REQUIRED_SETTINGS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
    "EVENTS_TABLE_NAME",
    "ROLES_TABLE_NAME",
    "SHIFTS_TABLE_NAME",
    "DYNAMODB_ENDPOINT_URL",
)


def ensure_settings() -> dict[str, str]:
    """Load .env and return all required application settings."""
    load_dotenv()

    missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing required settings: " + ", ".join(missing)
        )

    return {name: os.environ[name] for name in REQUIRED_SETTINGS}