"""Open a role to view its shifts."""

from tests_ui.sample_events import HERITAGE_DAY_ID


def test_role_page_shows_event_shifts_and_availability(page, heritage_day):
    # page: pytest-playwright browser page.
    # heritage_day: sample with both open and taken trash-pickup shifts.
    page.goto(f"/role?eventId={HERITAGE_DAY_ID}&roleNumber=1")

    page.get_by_role("heading", name="Trash pickup").wait_for()
    assert page.locator("#event-name").inner_text() == heritage_day["name"]

    open_shift = page.get_by_role("link", name="10:00 AM – 12:00 PM")
    open_shift.wait_for()
    assert open_shift.get_by_text("Open").is_visible()

    taken = page.locator(".choice.is-occupied").filter(has_text="8:00 AM – 10:00 AM")
    taken.wait_for()
    assert taken.get_by_text("Jack").is_visible()


def test_open_shift_opens_confirm_page(page, heritage_day):
    page.goto(f"/role?eventId={HERITAGE_DAY_ID}&roleNumber=1")
    page.get_by_role("link", name="10:00 AM – 12:00 PM").click()

    page.wait_for_url(
        f"**/confirm?eventId={HERITAGE_DAY_ID}&roleNumber=1&shiftNumber=2"
    )
    page.get_by_text("Confirm your enlistment").wait_for()


def test_role_page_shows_not_found_for_unknown_id(page, event_db):
    page.goto("/role?eventId=zzzzzzzz&roleNumber=1")
    error = page.locator("#page-error")
    error.wait_for()
    assert "not found" in error.inner_text().lower()
