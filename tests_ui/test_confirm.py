"""Sign up for an open shift."""


def test_signup_returns_to_role_page(page, heritage_day):
    # page: pytest-playwright browser page.
    # heritage_day: trash pickup shift 2 is still open.
    page.goto(
        f"/confirm?eventId={heritage_day['eventId']}&roleNumber=1&shiftNumber=2"
    )

    page.locator("#volunteer-name").fill("Alex Morgan")
    page.get_by_role("button", name="Submit").click()

    page.wait_for_url(
        f"**/role?eventId={heritage_day['eventId']}&roleNumber=1"
    )
    taken = page.locator(".choice.is-occupied").filter(
        has_text="10:00 AM – 12:00 PM"
    )
    taken.wait_for()
    assert taken.get_by_text("Alex Morgan").is_visible()


def test_signup_shows_error_when_name_missing(page, heritage_day):
    page.goto(
        f"/confirm?eventId={heritage_day['eventId']}&roleNumber=1&shiftNumber=2"
    )
    page.get_by_role("button", name="Submit").click()

    error = page.locator("#form-error")
    error.wait_for()
    assert error.inner_text() == "Enter your name."
    assert "/confirm" in page.url


def test_confirm_page_shows_not_found_for_unknown_id(page, event_db):
    page.goto("/confirm?eventId=zzzzzzzz&roleNumber=1&shiftNumber=1")
    page.locator("#volunteer-name").fill("Alex Morgan")
    page.get_by_role("button", name="Submit").click()

    error = page.locator("#form-error")
    error.wait_for()
    assert "not found" in error.inner_text().lower()
