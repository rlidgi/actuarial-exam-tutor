def test_get_course_requires_auth(client):
    resp = client.get("/api/courses/P")
    assert resp.status_code == 401


def test_get_course_returns_html_for_known_exam(client, db, register_user):
    resp_json = register_user("manual@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    for exam_code in ("P", "FM", "FAM"):
        resp = client.get(f"/api/courses/{exam_code}", headers=headers)
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/html")
        assert len(resp.data) > 1000


def test_get_course_unknown_exam_returns_404(client, db, register_user):
    resp_json = register_user("manualbad@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    resp = client.get("/api/courses/XX", headers=headers)

    assert resp.status_code == 404
