def role_id(role_number: int) -> str:
    """Return the stored, zero padded id for a 1-based role number."""
    return f"{role_number:02d}"


def role_key(event_id: str, role_number: int) -> str:
    """Return the Shifts partition key for a role."""
    return f"{event_id}#{role_id(role_number)}"
