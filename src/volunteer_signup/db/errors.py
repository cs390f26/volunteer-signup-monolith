from collections.abc import Iterator
from contextlib import contextmanager

from botocore.exceptions import BotoCoreError, ClientError


class DatabaseError(Exception):
    """The database could not complete the operation."""


class NotFoundError(Exception):
    """The requested event, role, or shift does not exist."""


class ShiftTakenError(Exception):
    """The shift already has a volunteer."""


class EventIdTakenError(Exception):
    """An event with the generated id already exists."""


@contextmanager
def database_errors() -> Iterator[None]:
    """Translate boto3 and botocore failures into DatabaseError."""
    try:
        yield
    except (ClientError, BotoCoreError) as error:
        raise DatabaseError(str(error)) from error
