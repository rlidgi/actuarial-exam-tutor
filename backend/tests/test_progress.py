from app.models import Exam, StudentProfile, Topic, User
from app.services import mastery_service, student_service


def _make_profile_with_topics(db):
    user = User(email="progress@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    gp_parent = Topic(exam_id=exam.id, name="General Probability", exam_weight=26.5)
    uv_parent = Topic(exam_id=exam.id, name="Univariate Random Variables", exam_weight=47.0)
    db.session.add_all([gp_parent, uv_parent])
    db.session.commit()

    t1 = Topic(
        exam_id=exam.id, name="Combinatorics", exam_weight=13.25, parent_topic_id=gp_parent.id
    )
    t2 = Topic(
        exam_id=exam.id, name="Expected Value", exam_weight=47.0, parent_topic_id=uv_parent.id
    )
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
    assert summary["next_recommended_topic"] in {"Combinatorics", "Expected Value"}


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
    assert summary["weakest_topic"] == "Expected Value"


def test_progress_summary_groups_topics_under_parent_categories(app, db):
    profile, exam, t1, t2 = _make_profile_with_topics(db)

    mastery_service.apply_mastery_update(
        profile, t1, mastery_service.PerformanceOutcome.CORRECT_INDEPENDENT, 0.9
    )

    summary = student_service.profile_progress_summary(profile)

    categories_by_name = {c["name"]: c for c in summary["categories"]}
    assert set(categories_by_name) == {"General Probability", "Univariate Random Variables"}

    gp_topics = {t["name"]: t for t in categories_by_name["General Probability"]["topics"]}
    # CORRECT_INDEPENDENT: +8 performance, +(0.9-0.5)*4=1.6 confidence, from 0 -> round(9.6) = 10.
    assert gp_topics["Combinatorics"]["mastery"] == 10
    assert gp_topics["Combinatorics"]["difficulty"] == 6

    uv_topics = {t["name"]: t for t in categories_by_name["Univariate Random Variables"]["topics"]}
    assert uv_topics["Expected Value"]["mastery"] is None  # not assessed in this test


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
    parent = Topic(exam_id=exam.id, name="General Probability", exam_weight=26.5)
    db.session.add(parent)
    db.session.commit()
    topic = Topic(
        exam_id=exam.id, name="Bayes Theorem & Total Probability", exam_weight=3.79,
        parent_topic_id=parent.id,
    )
    db.session.add(topic)
    db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)

    resp = client.get("/api/students/me/progress?exam=P", headers=headers)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["topics_total"] == 1
    assert body["next_recommended_topic"] == "Bayes Theorem & Total Probability"
    assert body["categories"] == [
        {
            "name": "General Probability",
            "exam_weight": 26.5,
            "topics": [
                {"name": "Bayes Theorem & Total Probability", "mastery": None, "difficulty": None}
            ],
        }
    ]
