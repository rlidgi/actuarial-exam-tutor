from app.models import Exam, StudentProfile, Topic, User
from app.services import mastery_service, student_service


def _make_profile_with_topics(db):
    user = User(email="progress@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    t1 = Topic(exam_id=exam.id, name="General Probability", exam_weight=26.5)
    t2 = Topic(exam_id=exam.id, name="Univariate Random Variables", exam_weight=47.0)
    db.session.add_all([t1, t2])
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    return profile, exam, t1, t2


def test_progress_summary_with_no_history(app, db):
    profile, exam, t1, t2 = _make_profile_with_topics(db)

    summary = student_service.profile_progress_summary(profile)

    assert summary["overall_mastery"] == 0
    assert summary["topics_studied"] == 0
    assert summary["topics_total"] == 2
    assert summary["weakest_topic"] is None
    assert summary["last_session_at"] is None
    assert summary["next_recommended_topic"] in {"General Probability", "Univariate Random Variables"}


def test_progress_summary_reflects_mastery_and_weakest_topic(app, db):
    profile, exam, t1, t2 = _make_profile_with_topics(db)

    mastery_service.apply_mastery_update(
        profile, t1, mastery_service.PerformanceOutcome.CORRECT_INDEPENDENT, 0.9
    )
    mastery_service.apply_mastery_update(
        profile, t2, mastery_service.PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION, 0.2
    )

    summary = student_service.profile_progress_summary(profile)

    assert summary["topics_studied"] == 2
    assert summary["weakest_topic"] == "Univariate Random Variables"


def test_progress_endpoint_requires_auth(client):
    resp = client.get("/api/students/me/progress?exam=P")
    assert resp.status_code == 401


def test_progress_endpoint_returns_summary(client, db):
    resp = client.post(
        "/api/auth/register", json={"email": "progressapi@example.com", "password": "secret123"}
    )
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exam = Exam(code="P", name="Exam P")
    db.session.add(exam)
    db.session.commit()
    topic = Topic(exam_id=exam.id, name="General Probability", exam_weight=26.5)
    db.session.add(topic)
    db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)

    resp = client.get("/api/students/me/progress?exam=P", headers=headers)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["topics_total"] == 1
    assert body["next_recommended_topic"] == "General Probability"
