from app.models import Exam, StudentProfile, Topic, User


def test_student_profile_unique_per_exam(app, db):
    user = User(email="a@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    db.session.add(StudentProfile(user_id=user.id, exam_id=exam.id))
    db.session.commit()

    assert StudentProfile.query.count() == 1


def test_topic_belongs_to_exam(app, db):
    exam = Exam(code="FM", name="Exam FM")
    db.session.add(exam)
    db.session.commit()

    topic = Topic(exam_id=exam.id, name="Annuities")
    db.session.add(topic)
    db.session.commit()

    assert topic.exam.code == "FM"
