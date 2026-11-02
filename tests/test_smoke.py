def test_home_renders(client, db, worldwide):
    response = client.get("/")
    assert response.status_code == 200


def test_language_redirect(client, db):
    response = client.generic("GET", "/support/")
    assert response.status_code == 200
