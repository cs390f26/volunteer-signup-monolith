from volunteer_signup.app import create_app


def test_health_returns_ok(db):
    app = create_app(db=db)
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_page_templates_render(db):
    app = create_app(db=db)
    client = app.test_client()

    for path in ("/", "/create", "/role", "/confirm"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"/static/styles.css" in response.data


def test_health_returns_unavailable_when_database_is_unreachable(db):
    db.delete_tables()
    app = create_app(db=db)
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
