from flask.testing import FlaskClient


def test_404_on_unknown_route(client: FlaskClient) -> None:
    response = client.get("/this/route/does/not/exist")
    assert response.status_code == 404


def test_upload_too_large_route(client: FlaskClient) -> None:
    # /upload-too-large is a real route that explicitly renders the 413 template,
    # used when nginx rejects an oversized upload before Flask sees it.
    response = client.get("/upload-too-large")
    assert response.status_code == 413
