import re
import secrets
import string
from datetime import date, datetime, timezone

from volunteer_signup.db.errors import (
    DatabaseError,
    EventIdTakenError,
    ShiftTakenError,
)
from volunteer_signup.db.errors import (
    NotFoundError as DatabaseNotFoundError,
)
from volunteer_signup.service.errors import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)

_EVENT_ID_CHARACTERS = string.ascii_lowercase + string.digits
_EVENT_ID_ATTEMPTS = 5


def _generate_event_id():
    return "".join(secrets.choice(_EVENT_ID_CHARACTERS) for _ in range(8))


def _utc_now():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _required_text(value, field_name, maximum):
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must contain between 1 and {maximum} characters"
        )

    value = value.strip()
    if not value or len(value) > maximum:
        raise ValidationError(
            f"{field_name} must contain between 1 and {maximum} characters"
        )

    return value


def _valid_date(value):
    if not isinstance(value, str):
        raise ValidationError("date must use YYYY-MM-DD format")

    value = value.strip()

    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(
            "date must be a valid date in YYYY-MM-DD format"
        ) from error

    if parsed.isoformat() != value:
        raise ValidationError("date must use YYYY-MM-DD format")

    return value


def _valid_time(value):
    if not isinstance(value, str):
        raise ValidationError("shift times must use HH:MM format")

    value = value.strip()

    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise ValidationError("shift times must use HH:MM format")

    return value


def _valid_shifts(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 50:
        raise ValidationError("shifts must contain between 1 and 50 items")

    shifts = []

    for shift in value:
        if not isinstance(shift, dict):
            raise ValidationError("each shift must be an object")

        start_time = _valid_time(shift.get("startTime"))
        end_time = _valid_time(shift.get("endTime"))

        if start_time >= end_time:
            raise ValidationError(
                "each shift must have a start time earlier than its end time"
            )

        shifts.append(
            {
                "startTime": start_time,
                "endTime": end_time,
            }
        )

    return shifts


def _valid_roles(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 10:
        raise ValidationError("roles must contain between 1 and 10 items")

    roles = []
    labels = set()

    for role in value:
        if not isinstance(role, dict):
            raise ValidationError("each role must be an object")

        label = _required_text(
            role.get("label"),
            "role label",
            100,
        )

        if label in labels:
            raise ValidationError("role labels must be distinct")

        labels.add(label)

        roles.append(
            {
                "label": label,
                "shifts": _valid_shifts(role.get("shifts")),
            }
        )

    return roles


class VolunteerSignupService:
    """Application rules and mapping between API and database formats."""

    def __init__(self, db, id_generator=None, clock=None):
        self.db = db
        self.id_generator = id_generator or _generate_event_id
        self.clock = clock or _utc_now

    def list_events(self):
        try:
            return self._list_events()
        except DatabaseError as error:
            raise ServiceUnavailableError(str(error)) from error

    def _list_events(self):
        events = sorted(
            self.db.list_events(),
            key=lambda event: event["createdAt"],
            reverse=True,
        )

        result = []
        for event in events:
            roles = [
                {
                    "number": int(role["roleId"]),
                    "label": role["label"],
                    "totalShifts": role["shiftCount"],
                    "openShifts": role["remainingShifts"],
                }
                for role in self.db.list_roles(event["eventId"])
            ]

            result.append(
                {
                    "id": event["eventId"],
                    "name": event["name"],
                    "description": event["description"],
                    "date": event["date"],
                    "roles": roles,
                }
            )

        return result

    def create_event(self, event_data):
        roles = _valid_roles(event_data.get("roles"))
        created_at = self.clock()
        name = _required_text(event_data.get("name"), "name", 100)
        description = _required_text(event_data.get("description"), "description", 280)
        event_date = _valid_date(event_data.get("date"))

        for _ in range(_EVENT_ID_ATTEMPTS):
            event_id = self.id_generator()
            event = {
                "eventId": event_id,
                "createdAt": created_at,
                "name": name,
                "description": description,
                "date": event_date,
            }

            try:
                self.db.create_event(event, roles)
            except EventIdTakenError:
                continue
            except DatabaseError as error:
                raise ServiceUnavailableError(str(error)) from error
            return event_id

        raise ServiceUnavailableError("unable to generate a unique event id")

    def get_role(self, event_id, role_number):
        try:
            event = self.db.get_event(event_id)

            if event is None:
                raise NotFoundError("event not found")

            role = self.db.get_role(event_id, role_number)

            if role is None:
                raise NotFoundError("role not found")

            shifts = self.db.list_shifts(event_id, role_number)
        except DatabaseError as error:
            raise ServiceUnavailableError(str(error)) from error

        mapped_shifts = []

        for shift in shifts:
            mapped_shift = {
                "number": shift["shiftNumber"],
                "startTime": shift["startTime"],
                "endTime": shift["endTime"],
                "available": "volunteerName" not in shift,
            }

            if "volunteerName" in shift:
                mapped_shift["volunteerName"] = shift["volunteerName"]

            mapped_shifts.append(mapped_shift)

        return {
            "eventId": event_id,
            "eventName": event["name"],
            "eventDate": event["date"],
            "number": role_number,
            "label": role["label"],
            "shifts": mapped_shifts,
        }

    def signup_for_shift(
        self,
        event_id,
        role_number,
        shift_number,
        volunteer_name,
    ):
        name = _required_text(
            volunteer_name,
            "name",
            100,
        )

        try:
            shift = self.db.sign_up(
                event_id,
                role_number,
                shift_number,
                name,
                self.clock(),
            )
        except DatabaseNotFoundError as error:
            raise NotFoundError(str(error)) from error
        except ShiftTakenError as error:
            raise ConflictError(str(error)) from error
        except DatabaseError as error:
            raise ServiceUnavailableError(str(error)) from error

        return {
            "number": shift["shiftNumber"],
            "startTime": shift["startTime"],
            "endTime": shift["endTime"],
            "available": False,
            "volunteerName": shift["volunteerName"],
        }
