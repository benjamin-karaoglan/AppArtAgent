"""Email service using Resend for transactional emails."""

import logging
from typing import Optional

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to: str,
    subject: str,
    html_body: str,
    attachments: Optional[list] = None,
) -> bool:
    """Send an email via Resend. Returns True on success, False on failure.

    Never raises — email delivery is best-effort.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email send")
        return False

    resend.api_key = settings.RESEND_API_KEY

    params: dict = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html_body,
    }

    if attachments:
        params["attachments"] = attachments

    try:
        resend.Emails.send(params)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception:
        logger.exception(f"Failed to send email to {to}: {subject}")
        return False
