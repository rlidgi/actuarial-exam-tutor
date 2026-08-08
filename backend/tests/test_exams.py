from app.models import Exam


def test_list_exams_returns_seeded_exams(client, db):
    exam = Exam(code="P", name="Exam P")
    db.session.add(exam)
    db.session.commit()

    resp = client.get("/api/exams")

    assert resp.status_code == 200
    assert resp.get_json()["exams"] == [{"code": "P", "name": "Exam P"}]


def test_list_exams_empty_when_none_seeded(client):
    resp = client.get("/api/exams")

    assert resp.status_code == 200
    assert resp.get_json()["exams"] == []
