import io
import json
from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, User


def _stream_events(text, response_id="resp_1"):
    delta_event = MagicMock(type="response.output_text.delta", delta=text)
    message_item = MagicMock(type="message")
    final_response = MagicMock(id=response_id, output=[message_item], output_text=text)
    completed_event = MagicMock(type="response.completed", response=final_response)
    return [delta_event, completed_event]


def _parse_sse(raw: str) -> list[dict]:
    return [json.loads(block[len("data: "):]) for block in raw.strip().split("\n\n") if block]


def _reply_text(raw: str) -> str:
    return "".join(e["delta"] for e in _parse_sse(raw) if "delta" in e)


def _register_with_profile(client, db, register_user, email):
    resp_json = register_user(email)
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)
    return headers


def test_send_message_json_body_still_works(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "jsonmsg@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_openai.return_value.responses.create.return_value = _stream_events("Sure thing.")
        resp = client.post(
            "/api/chat/message",
            json={"exam_code": "P", "message": "what is a sample space?"},
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"
    assert _reply_text(resp.get_data(as_text=True)) == "Sure thing."


def test_send_message_with_image_transcribes_and_combines_text(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "imgmsg@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai, \
         patch("app.api.chat.vision_service.downscale_image") as mock_downscale, \
         patch("app.api.chat.vision_service.transcribe_image") as mock_transcribe:
        mock_openai.return_value.responses.create.return_value = _stream_events("Here's the solution.")
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
    assert _reply_text(resp.get_data(as_text=True)) == "Here's the solution."
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


def test_send_message_rejects_non_image_attachment(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "badfile@example.com")

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
