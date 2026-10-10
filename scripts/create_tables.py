"""Create the Events, Roles, and Shifts tables if they do not already exist."""

from volunteer_signup.db import Database


def main() -> None:
    db = Database.from_env()
    db.create_tables()
    print(f"Tables ready: {db.events.name}, {db.roles.name}, {db.shifts.name}")


if __name__ == "__main__":
    main()
