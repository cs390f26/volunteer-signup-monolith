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


def test_unknown_route_returns_json_not_found():
    app = create_app()
    client = app.test_client()

    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Requested resource not found",
        }
    }


class UnexpectedFailureService:
    def list_events(self):
        raise RuntimeError("unexpected failure")


def test_unexpected_error_returns_json_internal_error():
    app = create_app(service=UnexpectedFailureService())
    client = app.test_client()

    response = client.get("/events")

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unable to complete the request",
        }
    }
