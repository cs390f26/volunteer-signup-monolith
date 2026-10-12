"""Create an event (and cancel / validation)."""


def test_create_event_returns_to_event_list(page, event_db):
    # page: pytest-playwright browser page.
    # event_db: start with no rows so the new event is easy to reason about.
    page.goto("/create")

    page.locator("#event-name").fill("Campus Cleanup")
    page.locator("#event-description").fill("Pick up litter around campus.")
    page.locator("#event-date").fill("2026-11-15")
    page.locator("#role-1-label").fill("Setup Crew")
    page.locator("#role-1-shift-1-start").fill("09:00")
    page.locator("#role-1-shift-1-end").fill("11:00")
    page.get_by_role("button", name="Create").click()

    page.wait_for_url("**/")
    page.get_by_role("heading", name="Campus Cleanup").wait_for()
    page.get_by_role("link", name="Setup Crew").wait_for()
    assert page.get_by_text("1 open").is_visible()


def test_cancel_returns_to_event_list(page, event_db):
    page.goto("/create")
    page.get_by_role("link", name="Cancel").click()
    page.wait_for_url("**/")
    page.get_by_role("link", name="Create event").wait_for()


def test_create_shows_error_when_name_missing(page, event_db):
    page.goto("/create")
    page.locator("#role-1-label").fill("Setup Crew")
    page.get_by_role("button", name="Create").click()

    error = page.locator("#form-error")
    error.wait_for()
    assert error.inner_text() == "Enter an event name."
    assert "/create" in page.url
