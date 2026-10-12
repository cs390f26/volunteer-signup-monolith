"""Sign up for an open shift."""

from tests_ui.sample_events import HERITAGE_DAY_ID


def test_signup_returns_to_role_with_name_shown(page, heritage_day):
    # page: pytest-playwright browser page.
    # heritage_day: trash pickup shift 2 is still open.
    page.goto(
        f"/confirm?eventId={HERITAGE_DAY_ID}&roleNumber=1&shiftNumber=2"
    )

    page.locator("#volunteer-name").fill("Alex Morgan")
    page.get_by_role("button", name="Submit").click()

    page.wait_for_url(f"**/role?eventId={HERITAGE_DAY_ID}&roleNumber=1")
    taken = page.locator(".choice.is-occupied").filter(
        has_text="10:00 AM – 12:00 PM"
    )
    taken.wait_for()
    assert taken.get_by_text("Alex Morgan").is_visible()


def test_signup_shows_error_when_name_missing(page, heritage_day):
    page.goto(
        f"/confirm?eventId={HERITAGE_DAY_ID}&roleNumber=1&shiftNumber=2"
    )
    page.get_by_role("button", name="Submit").click()

    error = page.locator("#form-error")
    error.wait_for()
    assert error.inner_text() == "Enter your name."
    assert "/confirm" in page.url


def test_confirm_page_shows_error_when_shift_missing(page, event_db):
    page.goto("/confirm")
    error = page.locator("#form-error")
    error.wait_for()
    assert error.inner_text() == "Missing shift."
