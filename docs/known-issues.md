# Known issues

Issues found in review that are not fixed yet.

## API routes (from PR #2)

1. `create_app()` defaults to `service=None`, so running the app makes every route except `/health` fail with an HTML 500. A real service class still needs to be written and wired in as the default.
2. `@events_bp.get("/events")` is applied twice in `src/volunteer_signup/app/routes/events.py`.
3. Unexpected exceptions and Flask's own 404s (for example `/events/x/roles/abc`, rejected by the `int` converter) return HTML instead of the `{"error": {...}}` JSON shape in `specs/openapi.yaml`. An app-wide error handler would fix this and remove the repeated JSON blocks in each route.
4. `tests/test_events_api.py` puts `totalShifts` in a role summary; `RoleSummary` in `specs/openapi.yaml` has only `number`, `label`, and `openShifts`.
5. The signup route validates the name itself and returns "Volunteer name is required", while the spec's message is "name must contain between 1 and 100 characters". Name validation belongs in the service.
6. Most new files are missing a trailing newline.

## Service layer

7. Nobody is assigned `service/` in `docs/process.md`, and it is what connects the routes to `db/`. It must:
   - match the interface the route tests use: `list_events()`, `create_event(data)`, `get_role(event_id, role_number)`, `signup_for_shift(event_id, role_number, shift_number, name)`;
   - translate db exceptions to service exceptions: `db.NotFoundError` to `service.NotFoundError`, `ShiftTakenError` to `ConflictError`, `DatabaseError` to `ServiceUnavailableError`;
   - generate a new id and retry on `EventIdTakenError`.

## Specs

8. `specs/db.md` says the health check calls `DescribeTable` on all three tables; `db.ping()` calls it on one table only, to stay cheap under frequent health probes.
9. `specs/db.md` writes roles and shifts before the conditional event `PutItem`, so a colliding id would overwrite a live event's roles and shifts before the condition fails. `db.create_event()` first checks that no event item and no role items use the id; the spec should describe that check.
10. `specs/db.md` says unprocessed batch items are retried with backoff. boto3's `batch_writer` resends them on its next flush without sleeping; only throttling errors get botocore's backoff.
