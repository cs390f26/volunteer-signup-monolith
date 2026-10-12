"""Wait until DynamoDB answers requests, or exit with an error after a timeout."""

import sys
import time

from botocore.exceptions import BotoCoreError, ClientError

from volunteer_signup.db import Database

TIMEOUT_SECONDS = 60


def main() -> None:
    db = Database.from_env()
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while True:
        try:
            db.client.list_tables(Limit=1)
            return
        except (BotoCoreError, ClientError):
            if time.monotonic() > deadline:
                sys.exit(f"DynamoDB was not reachable within {TIMEOUT_SECONDS} seconds")
            time.sleep(1)


if __name__ == "__main__":
    main()
