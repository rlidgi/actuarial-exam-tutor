from datetime import datetime, timedelta, timezone

from app.models import Exam, Message, Session, StudentProfile, User


def _login(client, email):
    resp = client.post(
        "/api/auth/register", json={"email": email, "password": "secret123"}
    )
    if resp.status_code != 201:
        resp = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_history_days_requires_auth(client):
    resp = client.get("/api/chat/history/days?exam=P")
    assert resp.status_code == 401


def test_history_days_groups_by_calendar_date(client, db):
    headers = _login(client, "historydays@example.com")
    exam = Exam(code="P", name="Exam P")
    db.session.add(exam)
    db.session.commit()
    user = User.query.filter_by(email="historydays@example.com").first()
    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    today = datetime.now(timezone.utc)
    week_ago = today - timedelta(days=7)

    db.session.add_all([
        Message(session_id=session.id, role="user", content="today's question", created_at=today),
        Message(
            session_id=session.id, role="user", content="old question", created_at=week_ago
        ),
    ])
    db.session.commit()

    resp = client.get("/api/chat/history/days?exam=P", headers=headers)

    assert resp.status_code == 200
    days = resp.get_json()["days"]
    assert days == [today.date().isoformat(), week_ago.date().isoformat()]


def test_history_day_returns_only_that_days_messages(client, db):
    headers = _login(client, "historyday@example.com")
    exam = Exam(code="P", name="Exam P")
    db.session.add(exam)
    db.session.commit()
    user = User.query.filter_by(email="historyday@example.com").first()
    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    today = datetime.now(timezone.utc)
    week_ago = today - timedelta(days=7)

    db.session.add_all([
        Message(session_id=session.id, role="user", content="old question", created_at=week_ago),
        Message(
            session_id=session.id, role="assistant", content="old reply",
            created_at=week_ago + timedelta(seconds=1),
        ),
        Message(session_id=session.id, role="user", content="today's question", created_at=today),
    ])
    db.session.commit()

    resp = client.get(
        f"/api/chat/history/day/{week_ago.date().isoformat()}?exam=P", headers=headers
    )

    assert resp.status_code == 200
    messages = resp.get_json()["messages"]
    assert messages == [
        {"role": "user", "content": "old question"},
        {"role": "assistant", "content": "old reply"},
    ]


def test_history_day_rejects_bad_date_format(client, db):
    headers = _login(client, "historybadformat@example.com")
    resp = client.get("/api/chat/history/day/not-a-date?exam=P", headers=headers)
    assert resp.status_code == 400
