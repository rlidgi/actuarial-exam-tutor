def test_register_then_login(client):
    resp = client.post(
        "/api/auth/register", json={"email": "student@example.com", "password": "secret123"}
    )
    assert resp.status_code == 201
    assert resp.json["access_token"]

    resp = client.post(
        "/api/auth/register", json={"email": "student@example.com", "password": "secret123"}
    )
    assert resp.status_code == 409

    resp = client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401

    resp = client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    assert resp.json["access_token"]


def test_register_requires_email_and_password(client):
    resp = client.post("/api/auth/register", json={"email": "", "password": ""})
    assert resp.status_code == 400
