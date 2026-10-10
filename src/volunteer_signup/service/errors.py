class ServiceUnavailableError(Exception):
    """Raised when an operation cannot complete because a dependency failed."""

class ValidationError(Exception):
    """Raised when submitted application data is invalid."""

class NotFoundError(Exception):
    """Raised when a requested event, role, or shift does not exist."""

class ConflictError(Exception):
    """Raised when the requested action conflicts with existing data."""