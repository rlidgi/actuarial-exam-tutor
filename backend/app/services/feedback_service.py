from app.extensions import db
from app.models.feedback import CATEGORIES, Feedback
from app.models.user import User

_RATING_FIELDS = ("overall_rating", "tutor_quality_rating", "ease_of_use_rating", "value_rating")
_DETAIL_FIELDS = ("overall_detail", "tutor_quality_detail", "ease_of_use_detail", "value_detail")


def _validate_rating(value):
    """None passes through untouched (the question simply wasn't
    answered) -- every rating on the form is optional, see Feedback."""
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 5):
        raise ValueError("ratings must be integers from 1 to 5")
    return value


def _validate_detail(value):
    """Same optional-text handling as the general message field, just
    reused per rating question."""
    value = (value or "").strip() or None
    if value and len(value) > 2000:
        raise ValueError("detail is too long")
    return value


def submit_feedback(
    user: User,
    overall_rating=None,
    overall_detail=None,
    tutor_quality_rating=None,
    tutor_quality_detail=None,
    ease_of_use_rating=None,
    ease_of_use_detail=None,
    value_rating=None,
    value_detail=None,
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
    details = {
        "overall_detail": _validate_detail(overall_detail),
        "tutor_quality_detail": _validate_detail(tutor_quality_detail),
        "ease_of_use_detail": _validate_detail(ease_of_use_detail),
        "value_detail": _validate_detail(value_detail),
    }

    category = (category or "").strip() or None
    if category is not None and category not in CATEGORIES:
        raise ValueError("invalid category")

    message = (message or "").strip() or None
    if message and len(message) > 5000:
        raise ValueError("message is too long")

    if not any(ratings.values()) and not any(details.values()) and not category and not message:
        raise ValueError("please fill in at least one field")

    feedback = Feedback(
        user_id=user.id, category=category, message=message, **ratings, **details
    )
    db.session.add(feedback)
    db.session.commit()
    return feedback
