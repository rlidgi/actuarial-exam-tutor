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
            ]
        )
        _send_admin_notification(
            subject=f"Campus Ambassador application: {name} ({school})",
            reply_to=email,
            body=body,
        )
    except Exception:
        logger.exception("failed to send ambassador application from %s", email)


def send_club_sponsorship_email(name: str, email: str, university: str, event_dates: str) -> None:
    """Fired from the landing page's Actuarial Club sponsorship form --
    same best-effort pattern as send_contact_email."""
    if not current_app.config["SMTP_PASSWORD"]:
        logger.info("SMTP not configured -- skipping club sponsorship request from %s", email)
        return

    try:
        _send_admin_notification(
            subject=f"Actuarial Club sponsorship request: {university}",
            reply_to=email,
            body="\n".join(
                [
                    f"Name: {name}",
                    f"Email: {email}",
                    f"College/University: {university}",
                    f"Upcoming meeting/event date(s): {event_dates}",
                ]
            ),
        )
    except Exception:
        logger.exception("failed to send club sponsorship request from %s", email)


def send_feedback_request_email(
    user: User, unsubscribe_url: str, one_click_unsubscribe_url: str | None
) -> bool:
    """The one-time "we'd love your feedback" email, sent ~1 week after
    signup by feedback_request_service.send_due. Unlike the other senders
    here this reports success, since the caller only marks the user as sent
    when it actually went out (a failure gets retried on the next run)."""
    if not current_app.config["SMTP_PASSWORD"]:
        logger.info("SMTP not configured -- skipping feedback request to %s", user.email)
        return False

    frontend_url = current_app.config["FRONTEND_URL"]
    message = EmailMessage()
    message["Subject"] = "We'd love your feedback on Actuarial Exams Tutor"
    message["From"] = f"Actuarial Exams Tutor <{current_app.config['SMTP_USERNAME']}>"
    message["To"] = user.email
    # Lets Gmail/Outlook show their own "Unsubscribe" button; the https form
    # is RFC 8058 one-click (the mail client POSTs to it directly).
    unsubscribe_targets = [f"<mailto:{current_app.config['SMTP_USERNAME']}?subject=unsubscribe>"]
    if one_click_unsubscribe_url:
        unsubscribe_targets.insert(0, f"<{one_click_unsubscribe_url}>")
        message["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    message["List-Unsubscribe"] = ", ".join(unsubscribe_targets)
    message.set_content(_feedback_request_plain_text(frontend_url, unsubscribe_url))
    message.add_alternative(
        _feedback_request_html(frontend_url, unsubscribe_url), subtype="html"
    )

    try:
        with smtplib.SMTP(
            current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"]
        ) as server:
            server.starttls()
            server.login(current_app.config["SMTP_USERNAME"], current_app.config["SMTP_PASSWORD"])
            server.send_message(message)
    except Exception:
        logger.exception("failed to send feedback request to %s", user.email)
        return False
    return True


def _feedback_request_plain_text(frontend_url: str, unsubscribe_url: str) -> str:
    return f"""Hi there,

Thanks for registering on our platform.

We built AET to provide actuarial students with the kind of personalized support that can be difficult to get while studying independently -- a tutor that can answer questions, walk through problems step by step, explain difficult concepts in different ways, and adapt to each student's progress.

We're continually working to make the platform better, and feedback from students who have actually used it is one of the most valuable ways for us to do that.

We'd love to hear about your experience so far:

1. What have you found most useful?
2. What hasn't worked as well as you expected?
3. What features, improvements, or changes would make AET more useful to you?

Whether you've used AET extensively or only had a chance to try it a few times, your perspective is valuable to us.

Share your feedback: {frontend_url}/feedback
(For security, you'll be asked to log in first. After logging in, you'll be taken to the feedback form.)

Your feedback will directly help us decide what to improve and where to focus as we continue developing Actuarial Exams Tutor.

Thank you for registering with AET and for helping us build a better study experience for actuarial students.

Yaron
Founder, Actuarial Exams Tutor

---
You are receiving this email because you registered for Actuarial Exams Tutor.
Unsubscribe: {unsubscribe_url}
"""


def _feedback_request_question(number: int, text: str, last: bool = False) -> str:
    border = "" if last else " border-bottom:1px solid #edf0f4;"
    return f"""\
              <tr>
                <td style="padding:12px 0;{border}">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                    <tr>
                      <td valign="top" style="width:30px; padding-right:10px;">
                        <div style="width:24px; height:24px; border-radius:50%; background-color:#eaf2ff;
                                    text-align:center; line-height:24px; font-size:13px; font-weight:700; color:#2563eb;">
                          {number}
                        </div>
                      </td>
                      <td style="font-size:15.5px; line-height:1.6; color:#4b5563;">
                        {text}
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
"""


def _feedback_request_html(frontend_url: str, unsubscribe_url: str) -> str:
    questions = (
        _feedback_request_question(1, "What have you found most useful?")
        + _feedback_request_question(2, "What hasn't worked as well as you expected?")
        + _feedback_request_question(
            3,
            "What features, improvements, or changes would make AET more useful to you?",
            last=True,
        )
    )
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>We'd Love Your Feedback</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
       style="width:100%; margin:0; padding:0; background-color:#f4f6f9;">
  <tr>
    <td align="center" style="padding:35px 15px;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
             style="max-width:620px; width:100%; background-color:#ffffff; border-radius:12px; overflow:hidden;">
        <tr>
          <td align="center"
              style="padding:30px 30px 24px 30px; background-color:#ffffff; border-bottom:1px solid #e9edf2;">
            <a href="{frontend_url}" style="text-decoration:none; border:0;">
              <img src="{frontend_url}/logo.png" alt="Actuarial Exams Tutor" width="240"
                   style="display:block; width:240px; max-width:100%; height:auto; border:0; outline:none;">
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:42px 45px 40px 45px;">
            <h1 style="margin:0 0 20px 0; font-size:29px; line-height:1.25; font-weight:700; color:#111827;">
              We'd love your feedback
            </h1>
            <p style="margin:0 0 20px 0; font-size:16px; line-height:1.65; color:#4b5563;">
              Hi there,
            </p>
            <p style="margin:0 0 20px 0; font-size:16px; line-height:1.7; color:#4b5563;">
              Thanks for registering on our platform.
            </p>
            <p style="margin:0 0 20px 0; font-size:16px; line-height:1.7; color:#4b5563;">
              We built AET to provide actuarial students with the kind of personalized support
              that can be difficult to get while studying independently &mdash; a tutor that can answer
              questions, walk through problems step by step, explain difficult concepts in different
              ways, and adapt to each student's progress.
            </p>
            <p style="margin:0 0 28px 0; font-size:16px; line-height:1.7; color:#4b5563;">
              We're continually working to make the platform better, and feedback from students
              who have actually used it is one of the most valuable ways for us to do that.
            </p>
            <p style="margin:0 0 20px 0; font-size:17px; line-height:1.6; font-weight:700; color:#111827;">
              We'd love to hear about your experience so far.
            </p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="margin:0 0 28px 0;">
{questions}            </table>
            <p style="margin:0 0 28px 0; font-size:15.5px; line-height:1.7; color:#6b7280;">
              Whether you've used AET extensively or only had a chance to try it a few times,
              your perspective is valuable to us.
            </p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="margin:0 0 12px 0;">
              <tr>
                <td align="center" style="padding:6px 0 8px 0;">
                  <a href="{frontend_url}/feedback"
                     style="display:inline-block; background-color:#2563eb; color:#ffffff;
                            text-decoration:none; font-size:16px; font-weight:700; line-height:1;
                            padding:16px 30px; border-radius:7px; border:1px solid #2563eb;">
                    Share Your Feedback
                  </a>
                </td>
              </tr>
            </table>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="margin:0 0 30px 0;">
              <tr>
                <td align="center" style="padding:12px 18px; background-color:#f8fafc; border-radius:7px;">
                  <p style="margin:0; font-size:13.5px; line-height:1.55; color:#6b7280;">
                    <strong style="color:#4b5563;">Please note:</strong>
                    For security, you'll be asked to log in first. After logging in,
                    you'll be taken to the feedback form.
                  </p>
                </td>
              </tr>
            </table>
            <p style="margin:0 0 25px 0; font-size:16px; line-height:1.7; color:#4b5563;">
              Your feedback will directly help us decide what to improve and where to focus
              as we continue developing Actuarial Exams Tutor.
            </p>
            <p style="margin:0 0 18px 0; font-size:16px; line-height:1.7; color:#4b5563;">
              Thank you for registering with AET and for helping us build a better study experience
              for actuarial students.
            </p>
            <p style="margin:0; font-size:16px; line-height:1.55; color:#374151;">
              Yaron<br>
              <span style="color:#6b7280;">Founder, Actuarial Exams Tutor</span>
            </p>
          </td>
        </tr>
        <tr>
          <td align="center"
              style="padding:24px 30px; background-color:#f8fafc; border-top:1px solid #e9edf2;">
            <p style="margin:0 0 8px 0; font-size:12px; line-height:1.5; color:#9ca3af;">
              Actuarial Exams Tutor
            </p>
            <p style="margin:0; font-size:12px; line-height:1.5; color:#9ca3af;">
              <a href="{frontend_url}" style="color:#6b7280; text-decoration:none;">actuarialexamstutor.com</a>
            </p>
          </td>
        </tr>
      </table>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
             style="max-width:620px;">
        <tr>
          <td align="center" style="padding:18px 15px 0 15px;">
            <p style="margin:0; font-size:11px; line-height:1.5; color:#a3aab4;">
              You are receiving this email because you registered for Actuarial Exams Tutor.
              <a href="{unsubscribe_url}" style="color:#a3aab4; text-decoration:underline;">Unsubscribe</a>
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""


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
