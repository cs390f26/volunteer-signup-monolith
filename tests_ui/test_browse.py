"""Browse events when the tables already have data."""

from tests_ui.sample_events import FOOD_DRIVE_ID, HERITAGE_DAY_ID


def test_list_shows_event_name_description_and_open_shifts(page, food_drive):
    # page: pytest-playwright browser page.
    # food_drive: sample event loaded into an otherwise empty store.
    page.goto("/")

    card = page.locator("#event-list li").filter(has_text=food_drive["name"])
    card.wait_for()
    assert card.get_by_text(food_drive["description"]).is_visible()
    assert card.get_by_role("link", name="Sorting").is_visible()
    assert card.get_by_text("2 open").first.is_visible()
    assert card.get_by_role("link", name="Loading").is_visible()


def test_list_shows_newest_event_first(page, two_events_newest_first):
    # page: pytest-playwright browser page.
    # two_events_newest_first: (newer, older) — newer has the later createdAt.
    newer, older = two_events_newest_first
    page.goto("/")

    titles = page.locator(".detail-title")
    titles.first.wait_for()
    assert titles.count() == 2
    assert titles.nth(0).inner_text() == newer["name"]
    assert titles.nth(1).inner_text() == older["name"]


def test_role_link_opens_role_page(page, food_drive):
    page.goto("/")
    card = page.locator("#event-list li").filter(has_text=food_drive["name"])
    card.get_by_role("link", name="Sorting").click()

    page.wait_for_url(f"**/role?eventId={FOOD_DRIVE_ID}&roleNumber=1")
    page.get_by_role("heading", name="Sorting").wait_for()


def test_create_event_link_opens_create_page(page, sample_events):
    page.goto("/")
    page.get_by_role("link", name="Create event").click()

    page.wait_for_url("**/create")
    page.get_by_role("heading", name="Create an event").wait_for()


def test_zero_open_shifts_still_links_to_role(page, heritage_day):
    page.goto("/")
    card = page.locator("#event-list li").filter(has_text=heritage_day["name"])
    greeter = card.get_by_role("link", name="Greeter")
    greeter.wait_for()
    assert card.get_by_text("0 open").is_visible()
    greeter.click()

    page.wait_for_url(f"**/role?eventId={HERITAGE_DAY_ID}&roleNumber=2")
    page.get_by_role("heading", name="Greeter").wait_for()
