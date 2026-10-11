# Known Issues and Resolution History

This document records issues found during review and their current status.

## Resolved during integration

1. The application started with `service=None`.
   - Resolved by implementing `VolunteerSignupService` and wiring it into `create_app()`.

2. `GET /events` had the same route decorator twice.
   - Resolved by removing the duplicate decorator.

3. Flask-generated 404 and unexpected 500 responses returned HTML.
   - Resolved by adding application-wide JSON error handlers.

4. API tests included `totalShifts`, but OpenAPI did not.
   - Resolved by adding `totalShifts` to `RoleSummary` and its examples.

5. Signup name validation was duplicated in the route and service.
   - Resolved by moving name validation and trimming into the service layer.

6. New Python files had inconsistent formatting or missing trailing newlines.
   - Resolved by formatting the modified files with Ruff.

7. No service layer connected the routes to the database.
   - Resolved by implementing event listing, event creation, role retrieval, signup, validation, data mapping, ID generation, and database error translation.

8. The health check only checked the Events table.
   - Resolved by checking Events, Roles, and Shifts.

## Remaining documentation issues

1. `specs/db.md` should explicitly describe the pre-write event ID check performed by `db.create_event()` before role and shift items are written.

2. `specs/db.md` says unprocessed batch items are retried with backoff. The implementation uses Boto3's `batch_writer`, which automatically resends unprocessed items during later flushes, while Botocore handles throttling retries and backoff.
