"""Feedback API endpoint for bug reports and feature requests."""

import html as html_module
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.services.email import send_email

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory rate limiter: 5 requests per minute per IP
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # seconds


def _check_rate_limit(client_ip: str) -> None:
    now = time.monotonic()
    timestamps = _rate_limit_store[client_ip]
    # Prune old entries
    _rate_limit_store[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429, detail="Too many feedback submissions. Please try again later."
        )
    _rate_limit_store[client_ip].append(now)


class FeedbackType(str, Enum):
    bug_report = "bug_report"
    feature_request = "feature_request"
    general_feedback = "general_feedback"


FEEDBACK_TYPE_LABELS = {
    FeedbackType.bug_report: "Bug Report",
    FeedbackType.feature_request: "Feature Request",
    FeedbackType.general_feedback: "General Feedback",
}


class FeedbackResponse(BaseModel):
    status: str
    message: str


def _build_feedback_html(
    feedback_type: FeedbackType,
    message: str,
    email: Optional[str],
    user_agent: Optional[str],
    screenshot_url: Optional[str],
) -> str:
    type_label = FEEDBACK_TYPE_LABELS[feedback_type]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    esc = html_module.escape

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
        <h2 style="color: #2563eb;">[{type_label}] AppArt Agent Feedback</h2>
        <hr style="border: 1px solid #e5e7eb;">

        <p><strong>Type:</strong> {type_label}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        {"<p><strong>From:</strong> " + esc(email) + "</p>" if email else ""}
        {"<p><strong>User Agent:</strong> <code>" + esc(user_agent) + "</code></p>" if user_agent else ""}

        <h3>Message</h3>
        <div style="background: #f9fafb; padding: 16px; border-radius: 8px; white-space: pre-wrap;">{esc(message)}</div>

        {"<h3>Screenshot</h3><p><a href='" + esc(screenshot_url) + "'>View Screenshot</a></p>" if screenshot_url else ""}
    </div>
    """
    return html


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: Request,
    type: FeedbackType = Form(...),
    message: str = Form(..., min_length=10),
    email: Optional[str] = Form(None),
    screenshot: Optional[UploadFile] = File(None),
):
    """Submit feedback, bug report, or feature request.

    No authentication required — anonymous feedback is welcome.
    Rate limited to 5 requests per minute per IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    user_agent = request.headers.get("user-agent")
    screenshot_url = None

    # Upload screenshot if provided
    if screenshot and screenshot.filename:
        try:
            from app.services.storage import get_storage_service

            storage = get_storage_service()
            file_data = await screenshot.read()
            content_type = screenshot.content_type or "image/png"
            filename = f"feedback/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{screenshot.filename}"
            storage.upload_file(
                file_data=file_data,
                filename=filename,
                content_type=content_type,
            )
            screenshot_url = storage.get_presigned_url(filename)
        except Exception:
            logger.exception("Failed to upload feedback screenshot")

    # Build and send email
    type_label = FEEDBACK_TYPE_LABELS[type]
    subject = f"[AppArt Agent] {type_label}: {message[:50]}"
    html_body = _build_feedback_html(type, message, email, user_agent, screenshot_url)

    if not settings.FEEDBACK_EMAIL:
        logger.warning("FEEDBACK_EMAIL not configured, feedback not delivered")
        return FeedbackResponse(
            status="received", message="Feedback received (email not configured)"
        )

    sent = send_email(
        to=settings.FEEDBACK_EMAIL,
        subject=subject,
        html_body=html_body,
    )

    if sent:
        return FeedbackResponse(status="sent", message="Thank you for your feedback!")
    else:
        return FeedbackResponse(status="received", message="Feedback received, thank you!")
