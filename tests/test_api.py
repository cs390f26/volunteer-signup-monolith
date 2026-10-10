from volunteer_signup.app import create_app


def test_health_returns_ok():
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_page_templates_render():
    app = create_app()
    client = app.test_client()

    for path in ("/", "/create", "/role", "/confirm"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"/static/styles.css" in response.data