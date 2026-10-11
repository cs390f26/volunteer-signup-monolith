import random
import time

from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from volunteer_signup.db.errors import (
    DatabaseError,
    EventIdTakenError,
    NotFoundError,
    ShiftTakenError,
    database_errors,
)
from volunteer_signup.db.keys import role_id, role_key

SIGNUP_ATTEMPTS = 4


def _role_and_shift_items(event_id: str, roles: list[dict]) -> tuple[list[dict], list[dict]]:
    """Build stored items, numbering roles and shifts in the order given."""
    role_items, shift_items = [], []
    for role_number, role in enumerate(roles, start=1):
        shifts = role["shifts"]
        role_items.append(
            {
                "eventId": event_id,
                "roleId": role_id(role_number),
                "label": role["label"],
                "shiftCount": len(shifts),
                "remainingShifts": len(shifts),
            }
        )
        for shift_number, shift in enumerate(shifts, start=1):
            shift_items.append(
                {
                    "roleKey": role_key(event_id, role_number),
                    "shiftNumber": shift_number,
                    "startTime": shift["startTime"],
                    "endTime": shift["endTime"],
                }
            )
    return role_items, shift_items


class WritesMixin:
    """Creating events and signing volunteers up for shifts."""

    def _event_id_in_use(self, event_id: str) -> bool:
        if "Item" in self.events.get_item(
            Key={"eventId": event_id}, ConsistentRead=True
        ):
            return True
        # Role items left by a failed creation would otherwise show up under the new event.
        page = self.roles.query(
            KeyConditionExpression=Key("eventId").eq(event_id),
            ConsistentRead=True,
            Limit=1,
        )
        return bool(page["Items"])

    def create_event(self, event: dict, roles: list[dict]) -> None:
        """Store an event with its roles and shifts.

        `event` is the complete Events item (eventId, createdAt, name,
        description, date). Each role is {"label", "shifts"}, and each shift is
        {"startTime", "endTime"}, in display order. Raises EventIdTakenError
        if the id is already used, so the caller can retry with a new one.
        """
        event_id = event["eventId"]
        role_items, shift_items = _role_and_shift_items(event_id, roles)

        with database_errors():
            if self._event_id_in_use(event_id):
                raise EventIdTakenError(event_id)

            with self.roles.batch_writer() as writer:
                for item in role_items:
                    writer.put_item(Item=item)
            with self.shifts.batch_writer() as writer:
                for item in shift_items:
                    writer.put_item(Item=item)

            try:
                self.events.put_item(
                    Item=event,
                    ConditionExpression="attribute_not_exists(eventId)",
                )
            except ClientError as error:
                if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    raise EventIdTakenError(event_id) from error
                raise

    def sign_up(
        self,
        event_id: str,
        role_number: int,
        shift_number: int,
        name: str,
        signed_up_at: str,
    ) -> dict:
        """Record a volunteer on an open shift and return the updated shift.

        Raises NotFoundError if the shift does not exist, ShiftTakenError if
        it already has a volunteer, and DatabaseError for anything else.
        """
        request = {
            "TransactItems": [
                {
                    "Update": {
                        "TableName": self.shifts.name,
                        "Key": {
                            "roleKey": role_key(event_id, role_number),
                            "shiftNumber": shift_number,
                        },
                        "UpdateExpression": "SET volunteerName = :name, signedUpAt = :at",
                        "ConditionExpression": (
                            "attribute_exists(roleKey) AND attribute_not_exists(volunteerName)"
                        ),
                        "ExpressionAttributeValues": {
                            ":name": name,
                            ":at": signed_up_at,
                        },
                        "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
                    }
                },
                {
                    "Update": {
                        "TableName": self.roles.name,
                        "Key": {
                            "eventId": event_id,
                            "roleId": role_id(role_number),
                        },
                        "UpdateExpression": "ADD remainingShifts :minusOne",
                        "ConditionExpression": "remainingShifts > :zero",
                        "ExpressionAttributeValues": {
                            ":minusOne": -1,
                            ":zero": 0,
                        },
                    }
                },
            ]
        }

        for attempt in range(SIGNUP_ATTEMPTS):
            try:
                self.client.transact_write_items(**request)
                break
            except BotoCoreError as error:
                raise DatabaseError(str(error)) from error
            except ClientError as error:
                if error.response["Error"]["Code"] != "TransactionCanceledException":
                    raise DatabaseError(str(error)) from error
                reasons = error.response.get("CancellationReasons", [])
                codes = [reason.get("Code") for reason in reasons]
                shift_reason = reasons[0] if reasons else {}

                if shift_reason.get("Code") == "ConditionalCheckFailed":
                    if "Item" in shift_reason:
                        raise ShiftTakenError() from error
                    # Some DynamoDB emulators omit Item, so confirm with a read.
                    shift = self.get_shift(event_id, role_number, shift_number)
                    if shift is not None and "volunteerName" in shift:
                        raise ShiftTakenError() from error
                    raise NotFoundError() from error

                if "TransactionConflict" in codes and attempt < SIGNUP_ATTEMPTS - 1:
                    time.sleep(random.uniform(0, 0.05 * 2**attempt))
                    continue
                raise DatabaseError(str(error)) from error

        shift = self.get_shift(event_id, role_number, shift_number)
        if shift is None:
            raise DatabaseError("shift missing after signup")
        return shift
