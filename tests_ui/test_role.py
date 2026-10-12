"""Open a role to view its shifts."""


def test_role_page_shows_shifts_and_availability(page, heritage_day):
    # page: pytest-playwright browser page.
    # heritage_day: sample with a known taken shift and an open shift.
    page.goto(f"/role?eventId={heritage_day['eventId']}&roleNumber=1")

    page.get_by_role("heading", name="Trash pickup").wait_for()
    page.get_by_role("link", name="10:00 AM – 12:00 PM").wait_for()
    taken = page.locator(".choice.is-occupied").filter(has_text="8:00 AM – 10:00 AM")
    taken.wait_for()
    assert taken.get_by_text("Jack").is_visible()


def test_open_shift_navigates_to_confirm(page, heritage_day):
    page.goto(f"/role?eventId={heritage_day['eventId']}&roleNumber=1")
    page.get_by_role("link", name="10:00 AM – 12:00 PM").click()

    page.wait_for_url(
        f"**/confirm?eventId={heritage_day['eventId']}&roleNumber=1&shiftNumber=2"
    )
    page.get_by_text("Confirm your enlistment").wait_for()


def test_role_page_shows_not_found_for_unknown_id(page, event_db):
    page.goto("/role?eventId=zzzzzzzz&roleNumber=1")
    error = page.locator("#page-error")
    error.wait_for()
    assert "not found" in error.inner_text().lower()
