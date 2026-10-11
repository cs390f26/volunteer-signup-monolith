import json
from decimal import Decimal
from pathlib import Path

from volunteer_signup.db.errors import database_errors


def read_seed_file(path: Path) -> dict[str, list[dict]]:
    """Read a sample data file with "events", "roles", and "shifts" lists."""
    with open(path, encoding="utf-8") as file:
        return json.load(file, parse_float=Decimal)


class SeedMixin:
    """Bulk loading of stored items, used by the seed script and tests."""

    def load_items(self, data: dict[str, list[dict]]) -> dict[str, int]:
        """Write the items as given and return how many went into each table."""
        # Events go last so a partly loaded event never appears in a Scan of Events.
        batches = [
            (self.roles, data.get("roles", [])),
            (self.shifts, data.get("shifts", [])),
            (self.events, data.get("events", [])),
        ]
        with database_errors():
            for table, items in batches:
                with table.batch_writer() as writer:
                    for item in items:
                        writer.put_item(Item=item)
        return {table.name: len(items) for table, items in batches}
