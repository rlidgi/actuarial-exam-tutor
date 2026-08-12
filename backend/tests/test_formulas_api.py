def test_get_formula_sheet_requires_auth(client):
    resp = client.get("/api/formulas/P")
    assert resp.status_code == 401


def test_get_formula_sheet_returns_html_for_known_exam(client, db, register_user):
    resp_json = register_user("formulas@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    for exam_code in ("P", "FM", "FAM"):
        resp = client.get(f"/api/formulas/{exam_code}", headers=headers)
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/html")
        assert len(resp.data) > 1000


def test_get_formula_sheet_unknown_exam_returns_404(client, db, register_user):
    resp_json = register_user("formulasbad@example.com")
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    resp = client.get("/api/formulas/XX", headers=headers)

    assert resp.status_code == 404
