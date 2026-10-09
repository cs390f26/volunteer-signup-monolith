# Use cases

Anyone can create an event made up of roles, which are made up of shifts. Anyone can also sign up for an open shift by submitting a name; no account, sign-in, or identity verification is required. The submitted name is stored and displayed when the shift is taken.

An `event` has a name, description, date, and 1–10 roles. A `role` is a position within an event and has a distinct label and 1–50 shifts. Each `shift` has a start time and end time and can be filled by exactly one volunteer. Once an event is created, its roles and shifts cannot be added, changed, or removed. Role and shift order is set at creation and remains the same everywhere they are displayed.

---

## Browse Events

A user opens the application to see what events exist.

They see all events, newest first. Each entry shows the event's name, description, and date, followed by its roles and the number of open shifts for each role. If no events exist, the list is empty.

Clicking a role opens the Role Details screen for that role. The Browse Events screen also has a way to create a new event.

### Scenarios

- **Empty list**: No events exist, so the list is empty, but the create-event option is still shown.
- **List with data**: Each entry shows the event's name, description, and date, followed by its roles and each role's remaining shifts.
- **Newest first**: With more than one event, the most recently created one appears first.
- **Open role details**: Clicking a role opens the Role Details screen for that role.
- **Create event**: Choosing "create event" opens the event creation flow.
- **System error**: If the application cannot retrieve events because the server or database is unavailable, the user sees a general error message. The failure is not displayed as an empty event list.

---

## Create an Event

Someone wants to set up a new one-day event for volunteers to sign up for.

They provide:

- a name (at most 100 characters)
- a description (at most 280 characters)
- a valid date
- between one and ten roles
- a distinct label for each role (at most 100 characters)
- between one and fifty shifts for each role
- a start time and end time for each shift

Each shift takes place on the event's date. A shift's start time must be earlier than its end time.

The system creates the event and returns the user to the Browse Events screen. The new event appears first, with its roles and available shifts displayed.

If the user cancels, they return to the Browse Events screen without creating anything.

### Scenarios

- **Successful create**: The user submits a valid name, description, date, roles, and shifts. The system creates the complete event and returns to the Browse Events screen.
- **Cancel**: The user leaves the create flow without submitting. They return to the Browse Events screen, and no event is created.
- **Invalid event input**: If the name, description, or date is missing or invalid, creation fails and the user is told which input must be corrected.
- **Invalid role input**: If there are fewer than one or more than ten roles, or if a role label is missing, too long, or repeated, creation fails.
- **Invalid shift input**: If a role has fewer than one or more than fifty shifts, if a start or end time is missing, or if a start time is not earlier than its end time, creation fails.
- **System error**: If the event cannot be stored because of a server or database failure, the user sees a general error message. No partial event is ever shown to users.

---

## Role Details

Someone selects a role from the Browse Events screen to view its shifts.

They see the event's name and date, the role's label, and its shifts in creation order. Each shift displays its start time, end time, and current availability.

An open shift can be selected and takes the user to the Signup screen. A taken shift displays the submitted volunteer name and is greyed out or otherwise shown as non-selectable.

If the requested role does not exist, the user is told that it was not found.

### Scenarios

- **Role details page**: For an existing role, the user sees the event's name and date, the role label, and all shifts in creation order.
- **Available shift**: An open shift displays its start and end times and can be selected to open the Signup screen.
- **Taken shift**: A filled shift displays its start and end times and the submitted volunteer name. It is visually disabled and cannot be selected.
- **Unknown role**: If the role identifier does not exist, the user is told that the role was not found.
- **System error**: If the role and its shifts cannot be retrieved because of a server or database failure, the user sees a general error message instead of incomplete role data.

---

## Sign Up for a Shift

Someone selects an open shift and enters a name.

The system trims and validates the submitted name. If the shift is still available, the system records the name on that shift and returns the user to the Role Details screen. The shift is then displayed as taken, shows the submitted volunteer name, and can no longer be selected.

Because there are no user accounts or identity verification, the system does not verify whether the submitted name belongs to the person completing the form.

### Scenarios

- **Successful signup**: The user submits a valid name for an open shift. The system records the name and returns to the Role Details screen, where the shift is shown as taken.
- **Already taken**: The shift was filled before the signup was submitted. The signup fails, the existing volunteer name is not overwritten, and the user is told that the shift is no longer available.
- **Concurrent signup conflict**: Two users attempt to take the same shift at nearly the same time. Only the first completed signup succeeds. The other signup fails as unavailable, and the first volunteer's name remains stored.
- **Unknown shift**: If the shift identifier does not exist, the signup fails and the user is told that the shift was not found.
- **Invalid name**: If the submitted name is missing, blank after trimming, or longer than 100 characters, the signup fails. The user remains on the Signup screen and is told to correct the name.
- **System error**: If the signup cannot be stored because of a server or database failure, the user sees a general error message. The shift remains unchanged, and the application does not display a successful signup.

---