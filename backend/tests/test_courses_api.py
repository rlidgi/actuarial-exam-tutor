def test_get_course_requires_auth(client):
    resp = client.get("/api/courses/P")
    assert resp.status_code == 401


def test_get_course_returns_html_for_known_exam(client, db):
    resp = client.post(
        "/api/auth/register", json={"email": "manual@example.com", "password": "secret123"}
    )
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/courses/P", headers=headers)

    assert resp.status_code == 200
    assert resp.content_type.startswith("text/html")
    assert len(resp.data) > 1000


def test_get_course_unknown_exam_returns_404(client, db):
    resp = client.post(
        "/api/auth/register", json={"email": "manualbad@example.com", "password": "secret123"}
    )
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/courses/FM", headers=headers)

    assert resp.status_code == 404
