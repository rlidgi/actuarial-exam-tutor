from app.extensions import db
from app.models.feedback import CATEGORIES, Feedback
from app.models.user import User

_RATING_FIELDS = ("overall_rating", "tutor_quality_rating", "ease_of_use_rating", "value_rating")


def _validate_rating(value):
    """None passes through untouched (the question simply wasn't
    answered) -- every rating on the form is optional, see Feedback."""
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 5):
        raise ValueError("ratings must be integers from 1 to 5")
    return value


def submit_feedback(
    user: User,
    overall_rating=None,
    tutor_quality_rating=None,
    ease_of_use_rating=None,
    value_rating=None,
    category: str | None = None,
    message: str | None = None,
) -> Feedback:
    """Validates and persists one /feedback submission. Every field is
    optional -- a rating alone, or a message alone, is still valid data --
    but a submission with nothing at all answered is rejected."""
    ratings = {
        "overall_rating": _validate_rating(overall_rating),
        "tutor_quality_rating": _validate_rating(tutor_quality_rating),
        "ease_of_use_rating": _validate_rating(ease_of_use_rating),
        "value_rating": _validate_rating(value_rating),
    }

    category = (category or "").strip() or None
    if category is not None and category not in CATEGORIES:
        raise ValueError("invalid category")

    message = (message or "").strip() or None
    if message and len(message) > 5000:
        raise ValueError("message is too long")

    if not any(ratings.values()) and not category and not message:
        raise ValueError("please fill in at least one field")

    feedback = Feedback(user_id=user.id, category=category, message=message, **ratings)
    db.session.add(feedback)
    db.session.commit()
    return feedback
