def test_get_formula_sheet_works_without_auth(client):
    for exam_code in ("P", "FM", "FAM"):
        resp = client.get(f"/api/formulas/{exam_code}")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/html")
        assert len(resp.data) > 1000


def test_get_formula_sheet_unknown_exam_returns_404(client):
    resp = client.get("/api/formulas/XX")

    assert resp.status_code == 404
