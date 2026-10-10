"""Load the sample data into DynamoDB, creating the tables if they are missing."""

import argparse
from pathlib import Path
from urllib.parse import urlparse

from volunteer_signup.config import ensure_settings
from volunteer_signup.db import Database, read_seed_file

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "specs" / "sample-data.json"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete and recreate the tables first (local endpoints only)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FILE,
        help=f"sample data file to load (default: {DEFAULT_FILE.name})",
    )
    args = parser.parse_args(argv)

    settings = ensure_settings()
    db = Database(settings)

    if args.reset:
        host = urlparse(settings["DYNAMODB_ENDPOINT_URL"]).hostname
        if host not in LOCAL_HOSTS:
            parser.error(f"--reset only runs against a local endpoint, not {host}")
        db.delete_tables()

    db.create_tables()
    counts = db.load_items(read_seed_file(args.file))
    print(", ".join(f"{name}: {count}" for name, count in counts.items()))


if __name__ == "__main__":
    main()
