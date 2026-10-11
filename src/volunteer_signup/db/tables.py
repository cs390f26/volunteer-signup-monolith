from botocore.exceptions import BotoCoreError, ClientError

from volunteer_signup.db.errors import database_errors


class TablesMixin:
    """Create, delete, and check the Events, Roles, and Shifts tables."""

    def _table_definitions(self) -> list[dict]:
        return [
            {
                "TableName": self.events.name,
                "KeySchema": [{"AttributeName": "eventId", "KeyType": "HASH"}],
                "AttributeDefinitions": [
                    {"AttributeName": "eventId", "AttributeType": "S"},
                ],
            },
            {
                "TableName": self.roles.name,
                "KeySchema": [
                    {"AttributeName": "eventId", "KeyType": "HASH"},
                    {"AttributeName": "roleId", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "eventId", "AttributeType": "S"},
                    {"AttributeName": "roleId", "AttributeType": "S"},
                ],
            },
            {
                "TableName": self.shifts.name,
                "KeySchema": [
                    {"AttributeName": "roleKey", "KeyType": "HASH"},
                    {"AttributeName": "shiftNumber", "KeyType": "RANGE"},
                ],
                "AttributeDefinitions": [
                    {"AttributeName": "roleKey", "AttributeType": "S"},
                    {"AttributeName": "shiftNumber", "AttributeType": "N"},
                ],
            },
        ]

    def _existing_table_names(self) -> set[str]:
        names = set()
        for page in self.client.get_paginator("list_tables").paginate():
            names.update(page["TableNames"])
        return names

    def create_tables(self) -> None:
        """Create any missing tables and wait until all of them are active."""
        with database_errors():
            existing = self._existing_table_names()
            for definition in self._table_definitions():
                if definition["TableName"] not in existing:
                    self.client.create_table(
                        **definition, BillingMode="PAY_PER_REQUEST"
                    )
            waiter = self.client.get_waiter("table_exists")
            for definition in self._table_definitions():
                waiter.wait(TableName=definition["TableName"])

    def delete_tables(self) -> None:
        """Delete any of the tables that exist and wait until they are gone."""
        with database_errors():
            existing = self._existing_table_names()
            names = [
                definition["TableName"]
                for definition in self._table_definitions()
                if definition["TableName"] in existing
            ]
            for name in names:
                self.client.delete_table(TableName=name)
            waiter = self.client.get_waiter("table_not_exists")
            for name in names:
                waiter.wait(TableName=name)

    def ping(self) -> bool:
        """Return whether the database is reachable and the Events table exists."""
        try:
            self.client.describe_table(TableName=self.events.name)
        except (ClientError, BotoCoreError):
            return False
        return True
