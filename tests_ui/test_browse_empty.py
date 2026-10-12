"""Browse events when the tables exist but have no items yet."""


def test_empty_list_shows_create_event_and_no_rows(page, event_db):
    # page comes from pytest-playwright; base_url is prepended to "/".
    # event_db clears the tables before this runs.
    page.goto("/")

    # get_by_role finds elements the way assistive tech does (here: a link
    # whose accessible name is "Create event"). Prefer this over CSS when you can.
    page.get_by_role("link", name="Create event").wait_for()
    assert page.locator("#event-list li").count() == 0
    assert page.locator("#list-status").is_hidden()
