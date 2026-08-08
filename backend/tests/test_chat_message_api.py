import io
from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, User


def _response_with_text(text):
    message_item = MagicMock(type="message")
    return MagicMock(output=[message_item], output_text=text)


def _register_with_profile(client, db, email):
    resp = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)
    return headers


def test_send_message_json_body_still_works(client, db):
    headers = _register_with_profile(client, db, "jsonmsg@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_openai.return_value.responses.create.return_value = _response_with_text("Sure thing.")
        resp = client.post(
            "/api/chat/message",
            json={"exam_code": "P", "message": "what is a sample space?"},
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.get_json()["reply"] == "Sure thing."


def test_send_message_with_image_transcribes_and_combines_text(client, db):
    headers = _register_with_profile(client, db, "imgmsg@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai, \
         patch("app.api.chat.vision_service.downscale_image") as mock_downscale, \
         patch("app.api.chat.vision_service.transcribe_image") as mock_transcribe:
        mock_openai.return_value.responses.create.return_value = _response_with_text("Here's the solution.")
        mock_downscale.return_value = (b"fake-jpeg-bytes", "image/jpeg")
        mock_transcribe.return_value = "A bag has 3 red and 2 blue balls..."

        resp = client.post(
            "/api/chat/message",
            data={
                "exam_code": "P",
                "message": "please solve this",
                "image": (io.BytesIO(b"fake-image-bytes"), "problem.png", "image/png"),
            },
            content_type="multipart/form-data",
            headers=headers,
        )

    assert resp.status_code == 200
    mock_downscale.assert_called_once()
    mock_transcribe.assert_called_once_with(b"fake-jpeg-bytes", "image/jpeg")

    user = User.query.filter_by(email="imgmsg@example.com").first()
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    last_user_message = (
        Message.query.join(Session, Message.session_id == Session.id)
        .filter(Session.student_profile_id == profile.id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .first()
    )
    assert last_user_message.content == "please solve this\n\nA bag has 3 red and 2 blue balls..."


def test_send_message_rejects_non_image_attachment(client, db):
    headers = _register_with_profile(client, db, "badfile@example.com")

    resp = client.post(
        "/api/chat/message",
        data={
            "exam_code": "P",
            "message": "",
            "image": (io.BytesIO(b"not an image"), "notes.txt", "text/plain"),
        },
        content_type="multipart/form-data",
        headers=headers,
    )

    assert resp.status_code == 400
