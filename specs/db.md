# DynamoDB data model

Volunteer signup data for this system is stored in **Amazon DynamoDB** across three tables: `Events`, `Roles`, and `Shifts`.

## Access patterns

- Create an event along with its roles and their shifts
- List all events, newest first
- List the roles of an event, each with its count of remaining shifts
- Get one role with its event's name and date and all of its shifts, in creation order
- Get one shift
- Sign a volunteer up for an open shift
- Check that the database is reachable (health check)

## Tables

| Table | Partition key | Sort key | Holds |
|-------|---------------|----------|-------|
| `Events` | `eventId` (S) | none | One item per event |
| `Roles` | `eventId` (S) | `roleId` (S) | One item per role, grouped under its event |
| `Shifts` | `roleKey` (S) | `shiftNumber` (N) | One item per shift, grouped under its role |

Each table is partitioned by its parent: an event's roles share a partition, and a role's shifts share a partition. A role's partition value is `roleKey`, the event id and role id joined by `#`, for example `"k7m2xq9p#01"`.

Sort keys are the sequence values assigned at creation, so DynamoDB returns roles and shifts in creation order with no sorting needed in application code. `roleId` is zero padded (`"01"` through `"10"`) because string sort keys order lexicographically; `shiftNumber` is a plain number because numeric sort keys order numerically.

Listing events uses a table **Scan** on `Events`; the application sorts those results in memory by `createdAt` descending to get newest first. A Scan returns at most 1 MB per call, so the application keeps scanning with `ExclusiveStartKey` until no `LastEvaluatedKey` is returned.

Every read (Scan, Query, and GetItem) uses `ConsistentRead=True`, so a new event or signup is visible on the very next page load.

An `eventId` from a URL that does not match `^[a-z0-9]{8}$` is reported as not found without reading the database. This also keeps `#` out of `roleKey`.

## `Events`

| Attribute | Type | Notes |
|-----------|------|--------|
| `eventId` | S | Partition key; 8 lowercase letters and digits, generated at creation with Python's `secrets` module |
| `createdAt` | S | UTC timestamp when the event was created (used when sorting newest first after a Scan) |
| `name` | S | Event name, at most 100 characters |
| `description` | S | Event description, at most 280 characters |
| `date` | S | The date of the event itself, `YYYY-MM-DD`, separate from `createdAt` |

Example item:

```json
{
  "eventId": "k7m2xq9p",
  "createdAt": "2026-09-18T14:05:00.000Z",
  "name": "Heritage Day",
  "description": "Heritage Day is a celebration of Moravian tradition, community, and service.",
  "date": "2026-09-24"
}
```

## `Roles`

One item per role. A Query on `eventId` returns all of an event's roles in creation order.

| Attribute | Type | Notes |
|-----------|------|--------|
| `eventId` | S | Partition key; the event this role belongs to |
| `roleId` | S | Sort key; zero padded sequence within the event (`"01"` through `"10"`) |
| `label` | S | Role label, at most 100 characters, distinct within the event |
| `shiftCount` | N | Total shifts for this role, 1 through 50; never changes |
| `remainingShifts` | N | How many of those shifts are still open; starts equal to `shiftCount` |

'shiftCount' and 'remainingShifts' let the Browse Events screen show each role's availability without reading any shift items, which matters because that screen lists every role of every event. The number of shifts already taken is `shiftCount` minus `remainingShifts`, so it is not stored.

`remainingShifts` is the only attribute anywhere on a role that ever changes, and it only ever decreases, by one per signup.

A role also does not store a `roleKey`, since it is just this item's two key values joined by `#`. The application builds it whenever it needs to reach the role's shifts.

Example item:

```json
{
  "eventId": "k7m2xq9p",
  "roleId": "01",
  "label": "Trash pickup",
  "shiftCount": 4,
  "remainingShifts": 2
}
```

## `Shifts`

One item per shift, partitioned by the role it belongs to. A Query on a single `roleKey` returns all of that role's shifts in creation order, which is exactly what the Role Details screen needs. A single shift is a GetItem on `roleKey` plus `shiftNumber`.

Role Details is therefore three reads: a GetItem on `Events` for the event name and date, a GetItem on `Roles` for the label, and this Query for the shifts. If either GetItem finds nothing, the role is not found.

| Attribute | Type | Notes |
|-----------|------|--------|
| `roleKey` | S | Partition key; the role this shift belongs to, as `eventId` and `roleId` joined by `#` |
| `shiftNumber` | N | Sort key; position of the shift within its role, 1 through 50 |
| `startTime` | S | Start time on the event's date, 24 hour `HH:MM`; never changes |
| `endTime` | S | End time on the event's date, 24 hour `HH:MM`, later than `startTime`; never changes |
| `volunteerName` | S | Name submitted at signup, at most 100 characters. **Absent when the shift is open** |
| `signedUpAt` | S | UTC timestamp of the signup. Absent when the shift is open |

A shift stores no event id or role id of its own. Both are already in `roleKey` and the application recovers them by splitting it on `#`.

Times are stored without a date or time zone because every shift takes place on its event's `date`. Zero padded `HH:MM` strings compare correctly as plain strings, so `startTime < endTime` can be checked without parsing.

A shift is taken if and only if `volunteerName` is present, so no separate status attribute is needed. Signups are anonymous: `volunteerName` is only the text the volunteer typed and is not tied to any account.

Example items, one taken and one open:

```json
{
  "roleKey": "k7m2xq9p#01",
  "shiftNumber": 1,
  "startTime": "08:00",
  "endTime": "10:00",
  "volunteerName": "Jordan",
  "signedUpAt": "2026-09-19T16:20:00.000Z"
}
```

```json
{
  "roleKey": "k7m2xq9p#01",
  "shiftNumber": 2,
  "startTime": "10:00",
  "endTime": "12:00"
}
```

## Writes

**Creating an event** writes the role and shift items first, then the event item last. Because an event can have up to 10 roles and 500 shifts, creation exceeds the 100 item limit of a single DynamoDB transaction, so the roles and shifts go out as a series of `BatchWriteItem` calls (25 items each). Writing the `Events` item last means a half written event never shows up in a Scan of `Events`, since the listing screen only learns event ids from that table.

Two properties of `BatchWriteItem` shape how this has to be done:

- It can return `UnprocessedItems` when it is throttled, so the writer retries those with backoff until nothing is left. Treating a partial batch as success would produce a role whose shifts are missing.
- It cannot carry a condition expression, and a put with an existing key silently overwrites that item. The event item is therefore written on its own with a `PutItem` conditioned on `attribute_not_exists(eventId)`, so a duplicate id fails loudly instead of replacing a live event (and stranding its roles under a new one).

A creation that fails partway leaves role and shift items with no event item pointing at them. Nothing can reach them, since every read path starts from an event id and those ids only come from `Events`, so they waste a little storage and nothing else.

**Signing up for a shift** is a `TransactWriteItems` of two operations:

1. An `UpdateItem` on the shift that sets `volunteerName` and `signedUpAt`, conditioned on `attribute_exists(roleKey) AND attribute_not_exists(volunteerName)`, with `ReturnValuesOnConditionCheckFailure` set to `ALL_OLD`.
2. An `UpdateItem` on the role of `ADD remainingShifts :minusOne`, conditioned on `remainingShifts > :zero`.

`attribute_exists(roleKey)` is needed because `UpdateItem` on a missing key creates the item; without it, signing up for a shift that does not exist would create one and decrement `remainingShifts`. On a missing role, `remainingShifts > :zero` already fails.

The shift condition also settles simultaneous signups: only one succeeds. One transaction keeps the shift and `remainingShifts` in step, and a cancelled transaction changes nothing.

If the transaction is cancelled, the application checks the shift's entry in `CancellationReasons` (index 0):

| Reason | API response |
|--------|--------------|
| `ConditionalCheckFailed`, no `Item` returned (shift does not exist) | 404 `NOT_FOUND` |
| `ConditionalCheckFailed`, `Item` returned (shift already taken) | 409 `SHIFT_TAKEN` |
| `TransactionConflict` (a simultaneous signup) | Retry a few times with backoff, then use the retry's result |
| Anything else | 500 `INTERNAL_ERROR` |

`TransactWriteItems` returns no item values, so after a successful signup the application does a GetItem on the shift to build the response.

Roles and shifts cannot be added, changed, or removed after an event is created, so this transaction is the only mutation in the system.

## Reading the Browse Events screen

Browse Events needs every event, its roles, and each role's count of open shifts. That is a Scan of `Events`, then one Query per event against `Roles`. The role items already carry `remainingShifts`, so the screen renders from those two levels of reads alone.

`Shifts` is never read for this screen. That is the reason the counts are stored: without them, every page load would have to read all of the shift items behind each role (up to 50 per role, and up to 500 per event) purely to count which ones were open, and DynamoDB charges for reading items even when a filter discards them before returning. The shift items themselves are only read on the Role Details screen, which genuinely needs them one role at a time.

## Health check

`GET /health` calls `DescribeTable` on each of the three tables. If any call fails, the API returns 503 `unavailable`.

## API names

The API uses different names and types than the stored items. The application converts between them:

| API | Stored |
|-----|--------|
| `id` / `eventId` | `eventId` |
| role `number` (integer, 1 through 10) | `roleId` (zero padded string, `"01"` through `"10"`) |
| shift `number` | `shiftNumber` |
| `openShifts` | `remainingShifts` |
| `available` | `true` when `volunteerName` is absent |
| `eventName`, `eventDate` | `name`, `date` on the `Events` item |
