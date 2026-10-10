class ServiceUnavailableError(Exception):
    """Raised when an operation cannot complete because a dependency failed."""

class ValidationError(Exception):
    """Raised when submitted application data is invalid."""