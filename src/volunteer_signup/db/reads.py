from collections.abc import Callable
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from volunteer_signup.db.errors import database_errors
from volunteer_signup.db.keys import role_id, role_key


def _from_dynamo(item: dict) -> dict:
    """Return the item with DynamoDB's Decimal numbers converted to int."""
    return {
        name: int(value) if isinstance(value, Decimal) else value
        for name, value in item.items()
    }


def _all_items(operation: Callable, page_size: int | None = None, **kwargs) -> list[dict]:
    """Run a Scan or Query, following LastEvaluatedKey until every page is read."""
    if page_size is not None:
        kwargs["Limit"] = page_size
    items = []
    while True:
        page = operation(ConsistentRead=True, **kwargs)
        items.extend(_from_dynamo(item) for item in page.get("Items", []))
        last_key = page.get("LastEvaluatedKey")
        if last_key is None:
            return items
        kwargs["ExclusiveStartKey"] = last_key


def _get(table, key: dict) -> dict | None:
    item = table.get_item(Key=key, ConsistentRead=True).get("Item")
    return _from_dynamo(item) if item is not None else None


class ReadsMixin:
    """Consistent reads of events, roles, and shifts."""

    def list_events(self, page_size: int | None = None) -> list[dict]:
        """Return every event, in no particular order."""
        with database_errors():
            return _all_items(self.events.scan, page_size)

    def get_event(self, event_id: str) -> dict | None:
        with database_errors():
            return _get(self.events, {"eventId": event_id})

    def list_roles(self, event_id: str) -> list[dict]:
        """Return an event's roles in creation order."""
        with database_errors():
            return _all_items(
                self.roles.query,
                KeyConditionExpression=Key("eventId").eq(event_id),
            )

    def get_role(self, event_id: str, role_number: int) -> dict | None:
        with database_errors():
            return _get(
                self.roles,
                {"eventId": event_id, "roleId": role_id(role_number)},
            )

    def list_shifts(self, event_id: str, role_number: int) -> list[dict]:
        """Return a role's shifts in creation order."""
        with database_errors():
            return _all_items(
                self.shifts.query,
                KeyConditionExpression=Key("roleKey").eq(
                    role_key(event_id, role_number)
                ),
            )

    def get_shift(
        self, event_id: str, role_number: int, shift_number: int
    ) -> dict | None:
        with database_errors():
            return _get(
                self.shifts,
                {
                    "roleKey": role_key(event_id, role_number),
                    "shiftNumber": shift_number,
                },
            )
