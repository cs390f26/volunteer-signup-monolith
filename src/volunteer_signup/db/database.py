import boto3
from botocore.config import Config

from volunteer_signup.config import ensure_settings

_BOTO_CONFIG = Config(
    connect_timeout=2,
    read_timeout=5,
    retries={"max_attempts": 3, "mode": "standard"},
)


class Database:
    """Access to the Events, Roles, and Shifts tables."""

    def __init__(self, settings: dict[str, str]):
        session = boto3.session.Session(
            aws_access_key_id=settings["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=settings["AWS_SECRET_ACCESS_KEY"],
            region_name=settings["AWS_DEFAULT_REGION"],
        )
        self.resource = session.resource(
            "dynamodb",
            endpoint_url=settings["DYNAMODB_ENDPOINT_URL"],
            config=_BOTO_CONFIG,
        )
        self.client = self.resource.meta.client
        self.events = self.resource.Table(settings["EVENTS_TABLE_NAME"])
        self.roles = self.resource.Table(settings["ROLES_TABLE_NAME"])
        self.shifts = self.resource.Table(settings["SHIFTS_TABLE_NAME"])

    @classmethod
    def from_env(cls) -> "Database":
        """Create a Database from .env and the process environment."""
        return cls(ensure_settings())
