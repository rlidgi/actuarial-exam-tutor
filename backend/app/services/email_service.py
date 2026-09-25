"""Transactional email via Namecheap Private Email's SMTP relay (see
app/config.py's SMTP_* settings). Kept as its own service, not folded into
user_service or auth.py, since sending mail is a distinct concern from
identity/account logic -- and the natural place to add more transactional
email later (e.g. a reward-earned notification).
"""
import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

from app.models.user import User
from app.services import referral_service

logger = logging.getLogger(__name__)


def send_welcome_email(user: User) -> None:
    """Called once, right after a brand-new signup (see auth.py's exchange
    route) -- best-effort, since a slow or failing mail send must never
    break the signup response. Silently no-ops if SMTP isn't configured
    (no SMTP_PASSWORD), same "optional, disabled when unconfigured" pattern
    as Langfuse tracing."""
    if not current_app.config["SMTP_PASSWORD"]:
        logger.info("SMTP not configured -- skipping welcome email to %s", user.email)
        return

    try:
        _send_welcome_email(user)
    except Exception:
        logger.exception("failed to send welcome email to %s", user.email)


def _send_welcome_email(user: User) -> None:
    frontend_url = current_app.config["FRONTEND_URL"]
    # Generated here (not left lazy) so a brand-new user's very first email
    # already has a working referral link, not a dead one -- see
    # referral_service.get_or_create_referral_code.
    referral_code = referral_service.get_or_create_referral_code(user)
    referral_url = f"{frontend_url}/?ref={referral_code}"

    message = EmailMessage()
    message["Subject"] = "Welcome to Actuarial Exams Tutor — Start Studying for Free"
    message["From"] = current_app.config["SMTP_USERNAME"]
    message["To"] = user.email
    message.set_content(_plain_text(frontend_url, referral_url))
    message.add_alternative(_html(frontend_url, referral_url), subtype="html")

    with smtplib.SMTP(current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"]) as server:
        server.starttls()
        server.login(current_app.config["SMTP_USERNAME"], current_app.config["SMTP_PASSWORD"])
        server.send_message(message)


def send_contact_email(name: str, from_email: str, message: str) -> None:
    """Fired from the public /contact page -- same best-effort, silently
    disabled when unconfigured pattern as send_welcome_email. Reply-To is
    set to the submitter's own address so admin@ can just hit reply."""
    if not current_app.config["SMTP_PASSWORD"]:
        logger.info("SMTP not configured -- skipping contact email from %s", from_email)
        return

    try:
        _send_admin_notification(
            subject=f"Contact form: {name}",
            reply_to=from_email,
            body=f"From: {name} <{from_email}>\n\n{message}",
        )
    except Exception:
        logger.exception("failed to send contact email from %s", from_email)


_CLUB_LABELS = {
    "yes": "Yes",
    "no": "No",
    "no_club": "School has no actuarial club",
}


def send_ambassador_application_email(
    name: str,
    email: str,
    school: str,
    graduation_year: str,
    actuarial_club: str,
    exams: str,
    message: str,
) -> None:
    """Fired from the public /ambassadors page's application form -- same
    best-effort pattern as send_contact_email, Reply-To set to the
    applicant so admin@ can reply directly."""
    if not current_app.config["SMTP_PASSWORD"]:
        logger.info("SMTP not configured -- skipping ambassador application from %s", email)
        return

    try:
        body = "\n".join(
            [
                f"Name: {name}",
                f"Email: {email}",
                f"School: {school}",
                f"Graduation year: {graduation_year or '(not given)'}",
                f"In actuarial club: {_CLUB_LABELS.get(actuarial_club, '(not given)')}",
                "",
                "Exams taken / currently studying for:",
                exams,
                "",
                "Why they want to be an ambassador:",
                message,
            ]
        )
        _send_admin_notification(
            subject=f"Campus Ambassador application: {name} ({school})",
            reply_to=email,
            body=body,
        )
    except Exception:
        logger.exception("failed to send ambassador application from %s", email)


_RATING_LABELS = {
    "overall_rating": "Overall experience",
    "tutor_quality_rating": "Tutor answer quality",
    "ease_of_use_rating": "Ease of use",
    "value_rating": "Value for price",
}

# Maps each *_rating field to its companion *_detail field, so the detail
# text can be printed right under its rating in the email body.
_DETAIL_FIELDS = {
    "overall_rating": "overall_detail",
    "tutor_quality_rating": "tutor_quality_detail",
    "ease_of_use_rating": "ease_of_use_detail",
    "value_rating": "value_detail",
}


def send_feedback_email(
    user: User, ratings: dict, details: dict, category: str | None, message: str | None
) -> None:
    """Fired from the /feedback page (logged-in users only) -- immediate
    visibility for a single submission. The Feedback row (see
    api/feedback.py) is the source of truth for aggregate analysis; this is
    best-effort and never blocks the request, same pattern as
    send_welcome_email. `ratings` and `details` are dicts of the four
    *_rating / *_detail fields, any of which may be None (every field on
    the form is optional)."""
    if not current_app.config["SMTP_PASSWORD"]:
        logger.info("SMTP not configured -- skipping feedback email from %s", user.email)
        return

    try:
        lines = [f"From: {user.email} (user id {user.id})"]
        for field, label in _RATING_LABELS.items():
            value = ratings.get(field)
            if value is not None:
                lines.append(f"{label}: {value}/5")
            detail = details.get(_DETAIL_FIELDS[field])
            if detail:
                lines.append(f"  -> {detail}")
        if category:
            lines.append(f"Category: {category}")
        body = "\n".join(lines)
        if message:
            body += f"\n\n{message}"

        overall = ratings.get("overall_rating")
        subject_bits = [f"{overall}/5" if overall is not None else "no rating"]
        if category:
            subject_bits.append(category)
        _send_admin_notification(
            subject=f"App feedback from {user.email} ({', '.join(subject_bits)})",
            reply_to=user.email,
            body=body,
        )
    except Exception:
        logger.exception("failed to send feedback email from %s", user.email)


def _send_admin_notification(subject: str, reply_to: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["SMTP_USERNAME"]
    message["To"] = "admin@actuarialexamstutor.com"
    message["Reply-To"] = reply_to
    message.set_content(body)

    with smtplib.SMTP(current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"]) as server:
        server.starttls()
        server.login(current_app.config["SMTP_USERNAME"], current_app.config["SMTP_PASSWORD"])
        server.send_message(message)


def _plain_text(frontend_url: str, referral_url: str) -> str:
    return f"""Hi there,

Welcome to Actuarial Exams Tutor! Your account is ready, and you can start studying right away.

As a registered user, you now have access to:

- Full study manuals for free -- Access the complete study manual for each supported actuarial exam.
- Free formula sheets -- Quick-reference formula sheets for each supported exam, condensed for fast lookup and last-minute review.
- 6 free AI Tutor messages -- Chance to try out the tutor. Ask questions about difficult concepts, formulas, practice problems, or anything else you need help understanding.
- Study at your own pace -- Use the study manuals whenever you need them throughout your exam preparation.

Get Started
The tutor will continuously track your proficiency across exam topics, identifies gaps in foundational knowledge, and use what it learns about your progress to guide you step by step toward exam mastery.

Your first 6 AI Tutor messages are free. After you've used your free messages, you can subscribe for unlimited access to the AI Tutor.

Start Studying: {frontend_url}

Refer a Friend & Earn $10
Know someone else studying for an actuarial exam?

Share your personal referral link and they'll receive 25% off their first month when they subscribe. For every successful referral, you'll receive a $10 credit toward your own subscription fees.

Your referral link: {referral_url}

You can find your personal referral link anytime on the Referrals page in your account. Simply copy it and share it with classmates, coworkers, study partners, or anyone else preparing for an actuarial exam.

They save 25%. You earn $10.

Good luck with your exam preparation, and welcome to Actuarial Exams Tutor!

The Actuarial Exams Tutor Team
"""


def _html(frontend_url: str, referral_url: str) -> str:
    return f"""\
<div style="background:#edefe8;padding:32px 16px;font-family:Georgia,'Times New Roman',serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;border:1px solid #d8dacd;">
    <div style="padding:28px 32px 4px;text-align:center;">
      <img src="{frontend_url}/logo.png" alt="Actuarial Exams Tutor" height="80" style="height:80px;width:auto;">
    </div>
    <div style="padding:12px 32px 32px;color:#172227;font-size:15px;line-height:1.6;">
      <p>Hi there,</p>
      <p>Welcome to Actuarial Exams Tutor! Your account is ready, and you can start studying right away.</p>
      <p>As a registered user, you now have access to:</p>
      <ul style="padding-left:20px;margin:0 0 16px;">
        <li style="margin-bottom:8px;"><strong>Full study manuals for free</strong> &mdash; Access the complete study manual for each supported actuarial exam.</li>
        <li style="margin-bottom:8px;"><strong>Free formula sheets</strong> &mdash; Quick-reference formula sheets for each supported exam, condensed for fast lookup and last-minute review.</li>
        <li style="margin-bottom:8px;"><strong>6 free AI Tutor messages</strong> &mdash; Chance to try out the tutor. Ask questions about difficult concepts, formulas, practice problems, or anything else you need help understanding.</li>
        <li style="margin-bottom:8px;"><strong>Study at your own pace</strong> &mdash; Use the study manuals whenever you need them throughout your exam preparation.</li>
      </ul>

      <h2 style="font-size:17px;color:#1f5c4d;margin:24px 0 8px;">Get Started</h2>
      <p>The tutor will continuously track your proficiency across exam topics, identifies gaps in foundational knowledge, and use what it learns about your progress to guide you step by step toward exam mastery.</p>
      <p>Your first 6 AI Tutor messages are free. After you've used your free messages, you can subscribe for unlimited access to the AI Tutor.</p>

      <div style="text-align:center;margin:24px 0;">
        <a href="{frontend_url}" style="display:inline-block;background:#1f5c4d;color:#ffffff;text-decoration:none;font-weight:bold;padding:12px 28px;border-radius:6px;font-family:Georgia,'Times New Roman',serif;">Start Studying</a>
      </div>

      <h2 style="font-size:17px;color:#1f5c4d;margin:24px 0 8px;">Refer a Friend &amp; Earn $10</h2>
      <p>Know someone else studying for an actuarial exam?</p>
      <p>Share your personal referral link and they'll receive 25% off their first month when they subscribe. For every successful referral, you'll receive a $10 credit toward your own subscription fees.</p>
      <p style="text-align:center;margin:20px 0;word-break:break-all;">
        <a href="{referral_url}" style="color:#1f5c4d;font-weight:bold;">{referral_url}</a>
      </p>
      <p>You can find your personal referral link anytime on the Referrals page in your account. Simply copy it and share it with classmates, coworkers, study partners, or anyone else preparing for an actuarial exam.</p>
      <p style="font-weight:bold;">They save 25%. You earn $10.</p>

      <p style="margin-top:24px;">Good luck with your exam preparation, and welcome to Actuarial Exams Tutor!</p>
      <p style="margin-bottom:0;">The Actuarial Exams Tutor Team</p>
    </div>
  </div>
</div>
"""
