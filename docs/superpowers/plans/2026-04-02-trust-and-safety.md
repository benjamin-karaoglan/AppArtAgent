# Trust & Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add legal pages, cookie consent, error pages, feedback system with email delivery, and a shared footer to make the app launch-ready.

**Architecture:** Frontend-heavy changes (new pages, components, i18n) plus one new backend endpoint (`POST /api/feedback`) backed by a Resend email service. No database changes. Cookie consent is fully client-side. The feedback endpoint is public (no auth required) with rate limiting.

**Tech Stack:** Next.js 14 (App Router), next-intl, Tailwind CSS, Lucide React, FastAPI, Resend Python SDK

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `frontend/src/components/ui/CookieConsent.tsx` | Cookie consent banner with accept/reject/manage |
| `frontend/src/components/ui/FeedbackButton.tsx` | Floating feedback trigger button |
| `frontend/src/components/ui/FeedbackModal.tsx` | Feedback form modal with type/message/screenshot/email |
| `frontend/src/components/ui/Footer.tsx` | Shared footer with legal links and feedback |
| `frontend/src/app/not-found.tsx` | Custom 404 page |
| `frontend/src/app/[locale]/error.tsx` | Custom 500 error boundary |
| `frontend/src/app/[locale]/legal/privacy/page.tsx` | Privacy policy page |
| `frontend/src/app/[locale]/legal/terms/page.tsx` | Terms of service page |
| `backend/app/services/email.py` | Resend email service wrapper |
| `backend/app/api/feedback.py` | Feedback API endpoint |
| `backend/tests/test_email_service.py` | Tests for email service |
| `backend/tests/test_feedback.py` | Tests for feedback endpoint |

### Modified Files

| File | Change |
|------|--------|
| `frontend/messages/en.json` | Add legal, cookie, feedback, error, footer translation keys |
| `frontend/messages/fr.json` | Add legal, cookie, feedback, error, footer translation keys |
| `frontend/src/app/[locale]/layout.tsx` | Add Footer and CookieConsent to layout |
| `frontend/src/app/[locale]/page.tsx` | Remove inline footer (replaced by shared Footer) |
| `frontend/src/components/PostHogProvider.tsx` | Gate initialization on cookie consent |
| `frontend/src/lib/api.ts` | Add feedbackAPI namespace |
| `backend/app/core/config.py` | Add RESEND_API_KEY, FEEDBACK_EMAIL, EMAIL_FROM settings |
| `backend/app/main.py` | Register feedback router |
| `backend/pyproject.toml` | Add resend dependency |
| `.env.example` | Add RESEND_API_KEY, FEEDBACK_EMAIL, EMAIL_FROM |

---

## Task 1: Add Backend Dependencies and Configuration

**Files:**

- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py:11-111`
- Modify: `.env.example`

- [ ] **Step 1: Add resend and slowapi to backend dependencies**

In `backend/pyproject.toml`, add to the `dependencies` list:

```toml
    "resend>=2.0.0",
```

- [ ] **Step 2: Add email config settings**

In `backend/app/core/config.py`, add these fields after the `LOGFIRE_ENABLED` line (after line 82):

```python
    # Email (Resend)
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    FEEDBACK_EMAIL: str = os.getenv("FEEDBACK_EMAIL", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "AppArt Agent <noreply@appartagent.com>")
```

- [ ] **Step 3: Add env vars to .env.example**

Append to `.env.example`:

```bash

# =============================================================================
# Email (Resend) — for feedback and notifications
# =============================================================================
# Sign up at https://resend.com and verify your domain to get an API key.
RESEND_API_KEY=
FEEDBACK_EMAIL=feedback@appartagent.com
EMAIL_FROM=AppArt Agent <noreply@appartagent.com>
```

- [ ] **Step 4: Install dependencies**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv sync`
Expected: dependencies install successfully

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app/core/config.py .env.example uv.lock
git commit -m "feat: add resend and slowapi deps, email config settings"
```

---

## Task 2: Email Service

**Files:**

- Create: `backend/app/services/email.py`
- Create: `backend/tests/test_email_service.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_email_service.py`:

```python
"""Tests for the email service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.email import send_email


class TestSendEmail:
    """Test email sending via Resend."""

    @patch("app.services.email.resend")
    @patch("app.services.email.settings")
    def test_send_email_success(self, mock_settings, mock_resend):
        mock_settings.RESEND_API_KEY = "re_test_123"
        mock_settings.EMAIL_FROM = "AppArt Agent <noreply@appartagent.com>"
        mock_resend.Emails.send.return_value = {"id": "email_123"}

        result = send_email(
            to="user@example.com",
            subject="Test Subject",
            html_body="<p>Hello</p>",
        )

        assert result is True
        mock_resend.Emails.send.assert_called_once_with(
            {
                "from": "AppArt Agent <noreply@appartagent.com>",
                "to": ["user@example.com"],
                "subject": "Test Subject",
                "html": "<p>Hello</p>",
            }
        )

    @patch("app.services.email.resend")
    @patch("app.services.email.settings")
    def test_send_email_no_api_key(self, mock_settings, mock_resend):
        mock_settings.RESEND_API_KEY = ""

        result = send_email(
            to="user@example.com",
            subject="Test",
            html_body="<p>Hello</p>",
        )

        assert result is False
        mock_resend.Emails.send.assert_not_called()

    @patch("app.services.email.resend")
    @patch("app.services.email.settings")
    def test_send_email_failure_returns_false(self, mock_settings, mock_resend):
        mock_settings.RESEND_API_KEY = "re_test_123"
        mock_settings.EMAIL_FROM = "AppArt Agent <noreply@appartagent.com>"
        mock_resend.Emails.send.side_effect = Exception("API error")

        result = send_email(
            to="user@example.com",
            subject="Test",
            html_body="<p>Hello</p>",
        )

        assert result is False

    @patch("app.services.email.resend")
    @patch("app.services.email.settings")
    def test_send_email_with_attachments(self, mock_settings, mock_resend):
        mock_settings.RESEND_API_KEY = "re_test_123"
        mock_settings.EMAIL_FROM = "AppArt Agent <noreply@appartagent.com>"
        mock_resend.Emails.send.return_value = {"id": "email_456"}

        attachments = [{"filename": "screenshot.png", "content": "base64data"}]
        result = send_email(
            to="user@example.com",
            subject="Test",
            html_body="<p>Hello</p>",
            attachments=attachments,
        )

        assert result is True
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["attachments"] == attachments
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv run pytest backend/tests/test_email_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.email'`

- [ ] **Step 3: Write the email service implementation**

Create `backend/app/services/email.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv run pytest backend/tests/test_email_service.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/email.py backend/tests/test_email_service.py
git commit -m "feat: add Resend email service with tests"
```

---

## Task 3: Feedback API Endpoint

**Files:**

- Create: `backend/app/api/feedback.py`
- Create: `backend/tests/test_feedback.py`
- Modify: `backend/app/main.py:1-82`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_feedback.py`:

```python
"""Tests for the feedback API endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestFeedbackEndpoint:
    """Test POST /api/feedback."""

    @patch("app.api.feedback.send_email")
    def test_submit_feedback_success(self, mock_send_email):
        mock_send_email.return_value = True

        response = client.post(
            "/api/feedback",
            data={
                "type": "bug_report",
                "message": "The price analysis page crashes when I click refresh",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sent"
        mock_send_email.assert_called_once()

        # Verify email content
        call_kwargs = mock_send_email.call_args
        assert "bug_report" in call_kwargs[1]["subject"].lower() or "bug_report" in call_kwargs[0][1].lower()

    @patch("app.api.feedback.send_email")
    def test_submit_feedback_with_email(self, mock_send_email):
        mock_send_email.return_value = True

        response = client.post(
            "/api/feedback",
            data={
                "type": "feature_request",
                "message": "It would be great to export analyses as PDF",
                "email": "user@example.com",
            },
        )

        assert response.status_code == 200

    def test_submit_feedback_missing_message(self):
        response = client.post(
            "/api/feedback",
            data={
                "type": "bug_report",
                "message": "",
            },
        )

        assert response.status_code == 422

    def test_submit_feedback_invalid_type(self):
        response = client.post(
            "/api/feedback",
            data={
                "type": "invalid_type",
                "message": "Some feedback message here",
            },
        )

        assert response.status_code == 422

    @patch("app.api.feedback.send_email")
    def test_submit_feedback_email_failure_still_returns_ok(self, mock_send_email):
        """Feedback submission should succeed even if email delivery fails."""
        mock_send_email.return_value = False

        response = client.post(
            "/api/feedback",
            data={
                "type": "general_feedback",
                "message": "Great app, love the price analysis feature!",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv run pytest backend/tests/test_feedback.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.api.feedback'`

- [ ] **Step 3: Write the feedback endpoint**

Create `backend/app/api/feedback.py`:

```python
"""Feedback API endpoint for bug reports and feature requests."""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.services.email import send_email

logger = logging.getLogger(__name__)

router = APIRouter()


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
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
        <h2 style="color: #2563eb;">[{type_label}] AppArt Agent Feedback</h2>
        <hr style="border: 1px solid #e5e7eb;">

        <p><strong>Type:</strong> {type_label}</p>
        <p><strong>Timestamp:</strong> {timestamp}</p>
        {"<p><strong>From:</strong> " + email + "</p>" if email else ""}
        {"<p><strong>User Agent:</strong> <code>" + user_agent + "</code></p>" if user_agent else ""}

        <h3>Message</h3>
        <div style="background: #f9fafb; padding: 16px; border-radius: 8px; white-space: pre-wrap;">{message}</div>

        {"<h3>Screenshot</h3><p><a href='" + screenshot_url + "'>View Screenshot</a></p>" if screenshot_url else ""}
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
    """
    user_agent = request.headers.get("user-agent")
    screenshot_url = None

    # Upload screenshot if provided
    if screenshot and screenshot.filename:
        try:
            from app.services.storage import get_storage_service

            storage = get_storage_service()
            file_data = await screenshot.read()
            content_type = screenshot.content_type or "image/png"
            filename = f"feedback/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{screenshot.filename}"
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
        return FeedbackResponse(status="received", message="Feedback received (email not configured)")

    sent = send_email(
        to=settings.FEEDBACK_EMAIL,
        subject=subject,
        html_body=html_body,
    )

    if sent:
        return FeedbackResponse(status="sent", message="Thank you for your feedback!")
    else:
        return FeedbackResponse(status="received", message="Feedback received, thank you!")
```

- [ ] **Step 4: Register the feedback router in main.py**

In `backend/app/main.py`, add the import (after line 8, with the other api imports):

```python
from app.api import analysis, documents, feedback, photos, properties, users, webhooks
```

And add the router inclusion (after line 82, after the webhooks router):

```python
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv run pytest backend/tests/test_feedback.py -v`
Expected: 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/feedback.py backend/tests/test_feedback.py backend/app/main.py
git commit -m "feat: add feedback API endpoint with email delivery"
```

---

## Task 4: Frontend i18n Keys

**Files:**

- Modify: `frontend/messages/en.json`
- Modify: `frontend/messages/fr.json`

- [ ] **Step 1: Add English translation keys**

Add the following top-level keys to `frontend/messages/en.json` (after the `"metadata"` key, before the closing `}`):

```json
  "legal": {
    "privacy": {
      "title": "Privacy Policy",
      "lastUpdated": "Last updated: April 2, 2026",
      "intro": "AppArt Agent (\"we\", \"us\", \"our\") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your personal data when you use our AI-powered apartment purchasing decision platform.",
      "controller": {
        "title": "1. Data Controller",
        "content": "AppArt Agent operates as the data controller for the personal data processed through our platform."
      },
      "dataCollected": {
        "title": "2. Data We Collect",
        "account": "Account information: name, email address, hashed password",
        "property": "Property details: addresses, prices, surface areas, room counts, and other property characteristics you enter",
        "documents": "Uploaded documents: PDFs and images of property-related documents (PV d'AG, diagnostics, tax notices, charges statements)",
        "photos": "Uploaded photos: apartment photos submitted for AI redesign",
        "generated": "AI-generated content: property analyses, document summaries, price estimations, and redesigned images",
        "usage": "Usage data: pages visited, features used (via PostHog analytics, only with your consent)",
        "technical": "Technical data: browser type, device information, IP address (for security and rate limiting)"
      },
      "purpose": {
        "title": "3. Purpose of Processing",
        "analysis": "Analyzing property documents and extracting key information using AI",
        "price": "Estimating property values by comparing with the DVF (Demandes de Valeurs Fonci\u00e8res) dataset",
        "redesign": "Generating interior redesign visualizations from your photos",
        "account": "Managing your account and providing access to your saved properties",
        "improvement": "Improving our services through anonymized analytics (with consent)"
      },
      "ai": {
        "title": "4. AI Processing",
        "content": "Your documents and photos are processed by Google Gemini (via Vertex AI) for analysis and image generation. This data is sent to Google's servers for processing. We do not use your data to train AI models. Google's data processing terms apply to this processing."
      },
      "storage": {
        "title": "5. Data Storage",
        "structured": "Structured data (account info, property details, analyses) is stored in PostgreSQL on Google Cloud SQL",
        "files": "Files (documents, photos, redesigns) are stored in Google Cloud Storage",
        "location": "All data is stored within the European Union or in regions compliant with EU data protection standards"
      },
      "cookies": {
        "title": "6. Cookies",
        "essential": "Essential cookies: session authentication, cookie consent preferences (always active)",
        "analytics": "Analytics cookies: PostHog tracking (opt-in only, disabled by default)"
      },
      "retention": {
        "title": "7. Data Retention",
        "content": "Your data is retained as long as your account is active. When you delete your account, all associated data (properties, documents, photos, analyses) is permanently deleted."
      },
      "rights": {
        "title": "8. Your Rights (GDPR)",
        "content": "Under the General Data Protection Regulation (GDPR), you have the right to:",
        "access": "Access your personal data",
        "rectification": "Rectify inaccurate data",
        "erasure": "Request erasure of your data (\"right to be forgotten\")",
        "portability": "Data portability",
        "objection": "Object to processing",
        "contact": "To exercise these rights, contact us at:"
      },
      "thirdParty": {
        "title": "9. Third-Party Services",
        "content": "We use the following third-party services:",
        "gcp": "Google Cloud Platform (hosting, storage, database)",
        "gemini": "Google Gemini / Vertex AI (AI analysis and image generation)",
        "posthog": "PostHog (analytics, opt-in only)",
        "resend": "Resend (transactional email delivery)",
        "betterAuth": "Better Auth (authentication)"
      },
      "changes": {
        "title": "10. Changes to This Policy",
        "content": "We may update this policy from time to time. We will notify registered users of significant changes via email."
      },
      "contactEmail": "privacy@appartagent.com"
    },
    "terms": {
      "title": "Terms of Service",
      "lastUpdated": "Last updated: April 2, 2026",
      "intro": "By using AppArt Agent, you agree to these Terms of Service. Please read them carefully.",
      "service": {
        "title": "1. Service Description",
        "content": "AppArt Agent is an AI-powered platform that helps apartment buyers in France make informed purchasing decisions by analyzing property documents, comparing prices with public market data (DVF), and generating interior redesign visualizations."
      },
      "aiDisclaimer": {
        "title": "2. AI Disclaimer",
        "content": "All analyses, estimates, and recommendations provided by AppArt Agent are for informational purposes only. They do not constitute professional legal, financial, or real estate advice. AI-generated content may contain errors or inaccuracies. Always consult qualified professionals before making purchasing decisions."
      },
      "userResponsibilities": {
        "title": "3. User Responsibilities",
        "accurate": "Provide accurate information about properties",
        "lawful": "Use the platform for lawful purposes only",
        "credentials": "Keep your account credentials secure",
        "rights": "Only upload documents and photos you have the right to use"
      },
      "ip": {
        "title": "4. Intellectual Property",
        "userContent": "You retain ownership of all content you upload (documents, photos). By uploading, you grant us a limited license to process this content for the purpose of providing our services.",
        "aiContent": "AI-generated content (analyses, redesigned images) is provided for your personal use. You may download and share it freely.",
        "platform": "The AppArt Agent platform, including its design, code, and features, remains our intellectual property."
      },
      "availability": {
        "title": "5. Service Availability",
        "content": "AppArt Agent is provided \"as is\" without warranty. We do not guarantee uninterrupted service availability. We may perform maintenance or updates that temporarily affect access."
      },
      "liability": {
        "title": "6. Limitation of Liability",
        "content": "To the maximum extent permitted by law, AppArt Agent shall not be liable for any indirect, incidental, or consequential damages arising from your use of the platform. This includes decisions made based on AI-generated analyses or estimates."
      },
      "termination": {
        "title": "7. Account Termination",
        "content": "We may suspend or terminate accounts that violate these terms. You may delete your account at any time, which will permanently remove all your data."
      },
      "law": {
        "title": "8. Governing Law",
        "content": "These terms are governed by French law. Any disputes shall be subject to the jurisdiction of French courts."
      },
      "changes": {
        "title": "9. Changes to These Terms",
        "content": "We may update these terms from time to time. Continued use of the platform after changes constitutes acceptance of the new terms."
      },
      "contactEmail": "legal@appartagent.com"
    }
  },
  "cookie": {
    "title": "Cookie Preferences",
    "description": "We use cookies to improve your experience. Essential cookies are required for the site to function. Analytics cookies help us understand how you use the app.",
    "acceptAll": "Accept All",
    "rejectNonEssential": "Reject Non-Essential",
    "managePreferences": "Manage Preferences",
    "savePreferences": "Save Preferences",
    "essential": {
      "title": "Essential Cookies",
      "description": "Required for authentication and basic functionality. Cannot be disabled."
    },
    "analytics": {
      "title": "Analytics Cookies",
      "description": "Help us understand how you use the app to improve it. Powered by PostHog."
    },
    "alwaysActive": "Always active"
  },
  "feedback": {
    "button": "Feedback",
    "title": "Send Feedback",
    "type": {
      "label": "Type",
      "bug_report": "Bug Report",
      "feature_request": "Feature Request",
      "general_feedback": "General Feedback"
    },
    "message": {
      "label": "Message",
      "placeholder": "Describe the issue or suggestion..."
    },
    "email": {
      "label": "Email (optional)",
      "placeholder": "your@email.com"
    },
    "screenshot": {
      "label": "Screenshot (optional)",
      "hint": "Drag & drop or click to upload an image (max 5MB)"
    },
    "submit": "Send Feedback",
    "submitting": "Sending...",
    "success": "Thank you! We'll review your feedback.",
    "error": "Failed to send feedback. Please try again."
  },
  "errors": {
    "notFound": {
      "title": "Page Not Found",
      "description": "The page you're looking for doesn't exist or has been moved.",
      "goHome": "Go Home",
      "goBack": "Go Back",
      "goDashboard": "Go to Dashboard"
    },
    "serverError": {
      "title": "Something Went Wrong",
      "description": "An unexpected error occurred. Please try again.",
      "tryAgain": "Try Again",
      "reportIssue": "Report This Issue",
      "details": "Error Details"
    }
  },
  "footer": {
    "copyright": "\u00a9 2026 AppArt Agent. All rights reserved.",
    "tagline": "AI-powered apartment purchasing decisions in France",
    "privacy": "Privacy Policy",
    "terms": "Terms of Service",
    "feedback": "Feedback"
  }
```

- [ ] **Step 2: Add French translation keys**

Add the same structure to `frontend/messages/fr.json` with French translations. The full French content (add after the `"metadata"` key):

```json
  "legal": {
    "privacy": {
      "title": "Politique de Confidentialit\u00e9",
      "lastUpdated": "Derni\u00e8re mise \u00e0 jour : 2 avril 2026",
      "intro": "AppArt Agent (\u00ab nous \u00bb, \u00ab notre \u00bb) s'engage \u00e0 prot\u00e9ger votre vie priv\u00e9e. Cette Politique de Confidentialit\u00e9 explique comment nous collectons, utilisons et prot\u00e9geons vos donn\u00e9es personnelles lorsque vous utilisez notre plateforme d'aide \u00e0 l'achat immobilier propuls\u00e9e par l'IA.",
      "controller": {
        "title": "1. Responsable du traitement",
        "content": "AppArt Agent agit en tant que responsable du traitement des donn\u00e9es personnelles trait\u00e9es via notre plateforme."
      },
      "dataCollected": {
        "title": "2. Donn\u00e9es collect\u00e9es",
        "account": "Informations de compte : nom, adresse email, mot de passe chiffr\u00e9",
        "property": "D\u00e9tails des biens : adresses, prix, surfaces, nombre de pi\u00e8ces et autres caract\u00e9ristiques que vous saisissez",
        "documents": "Documents t\u00e9l\u00e9vers\u00e9s : PDF et images de documents li\u00e9s au bien (PV d'AG, diagnostics, avis d'imposition, appels de charges)",
        "photos": "Photos t\u00e9l\u00e9vers\u00e9es : photos d'appartement soumises pour le redesign par IA",
        "generated": "Contenu g\u00e9n\u00e9r\u00e9 par l'IA : analyses de biens, r\u00e9sum\u00e9s de documents, estimations de prix et images redesign\u00e9es",
        "usage": "Donn\u00e9es d'utilisation : pages visit\u00e9es, fonctionnalit\u00e9s utilis\u00e9es (via PostHog, uniquement avec votre consentement)",
        "technical": "Donn\u00e9es techniques : type de navigateur, informations sur l'appareil, adresse IP (pour la s\u00e9curit\u00e9)"
      },
      "purpose": {
        "title": "3. Finalit\u00e9 du traitement",
        "analysis": "Analyser les documents immobiliers et extraire les informations cl\u00e9s gr\u00e2ce \u00e0 l'IA",
        "price": "Estimer la valeur des biens en comparant avec le jeu de donn\u00e9es DVF (Demandes de Valeurs Fonci\u00e8res)",
        "redesign": "G\u00e9n\u00e9rer des visualisations de r\u00e9novation int\u00e9rieure \u00e0 partir de vos photos",
        "account": "G\u00e9rer votre compte et fournir l'acc\u00e8s \u00e0 vos biens sauvegard\u00e9s",
        "improvement": "Am\u00e9liorer nos services gr\u00e2ce \u00e0 des analyses anonymis\u00e9es (avec consentement)"
      },
      "ai": {
        "title": "4. Traitement par l'IA",
        "content": "Vos documents et photos sont trait\u00e9s par Google Gemini (via Vertex AI) pour l'analyse et la g\u00e9n\u00e9ration d'images. Ces donn\u00e9es sont envoy\u00e9es aux serveurs de Google pour traitement. Nous n'utilisons pas vos donn\u00e9es pour entra\u00eener des mod\u00e8les d'IA. Les conditions de traitement des donn\u00e9es de Google s'appliquent."
      },
      "storage": {
        "title": "5. Stockage des donn\u00e9es",
        "structured": "Les donn\u00e9es structur\u00e9es (compte, d\u00e9tails des biens, analyses) sont stock\u00e9es dans PostgreSQL sur Google Cloud SQL",
        "files": "Les fichiers (documents, photos, redesigns) sont stock\u00e9s dans Google Cloud Storage",
        "location": "Toutes les donn\u00e9es sont stock\u00e9es au sein de l'Union Europ\u00e9enne ou dans des r\u00e9gions conformes aux normes de protection des donn\u00e9es de l'UE"
      },
      "cookies": {
        "title": "6. Cookies",
        "essential": "Cookies essentiels : authentification de session, pr\u00e9f\u00e9rences de cookies (toujours actifs)",
        "analytics": "Cookies analytiques : suivi PostHog (opt-in uniquement, d\u00e9sactiv\u00e9 par d\u00e9faut)"
      },
      "retention": {
        "title": "7. Conservation des donn\u00e9es",
        "content": "Vos donn\u00e9es sont conserv\u00e9es tant que votre compte est actif. Lorsque vous supprimez votre compte, toutes les donn\u00e9es associ\u00e9es (biens, documents, photos, analyses) sont d\u00e9finitivement supprim\u00e9es."
      },
      "rights": {
        "title": "8. Vos droits (RGPD)",
        "content": "En vertu du R\u00e8glement G\u00e9n\u00e9ral sur la Protection des Donn\u00e9es (RGPD), vous avez le droit de :",
        "access": "Acc\u00e9der \u00e0 vos donn\u00e9es personnelles",
        "rectification": "Rectifier les donn\u00e9es inexactes",
        "erasure": "Demander l'effacement de vos donn\u00e9es (\u00ab droit \u00e0 l'oubli \u00bb)",
        "portability": "Portabilit\u00e9 des donn\u00e9es",
        "objection": "Vous opposer au traitement",
        "contact": "Pour exercer ces droits, contactez-nous \u00e0 :"
      },
      "thirdParty": {
        "title": "9. Services tiers",
        "content": "Nous utilisons les services tiers suivants :",
        "gcp": "Google Cloud Platform (h\u00e9bergement, stockage, base de donn\u00e9es)",
        "gemini": "Google Gemini / Vertex AI (analyse IA et g\u00e9n\u00e9ration d'images)",
        "posthog": "PostHog (analytique, opt-in uniquement)",
        "resend": "Resend (envoi d'emails transactionnels)",
        "betterAuth": "Better Auth (authentification)"
      },
      "changes": {
        "title": "10. Modifications de cette politique",
        "content": "Nous pouvons mettre \u00e0 jour cette politique de temps en temps. Nous informerons les utilisateurs inscrits des changements importants par email."
      },
      "contactEmail": "privacy@appartagent.com"
    },
    "terms": {
      "title": "Conditions G\u00e9n\u00e9rales d'Utilisation",
      "lastUpdated": "Derni\u00e8re mise \u00e0 jour : 2 avril 2026",
      "intro": "En utilisant AppArt Agent, vous acceptez ces Conditions G\u00e9n\u00e9rales d'Utilisation. Veuillez les lire attentivement.",
      "service": {
        "title": "1. Description du service",
        "content": "AppArt Agent est une plateforme propuls\u00e9e par l'IA qui aide les acheteurs d'appartements en France \u00e0 prendre des d\u00e9cisions d'achat \u00e9clair\u00e9es en analysant les documents immobiliers, en comparant les prix avec les donn\u00e9es publiques du march\u00e9 (DVF), et en g\u00e9n\u00e9rant des visualisations de r\u00e9novation int\u00e9rieure."
      },
      "aiDisclaimer": {
        "title": "2. Avertissement IA",
        "content": "Toutes les analyses, estimations et recommandations fournies par AppArt Agent sont \u00e0 titre informatif uniquement. Elles ne constituent pas un conseil juridique, financier ou immobilier professionnel. Le contenu g\u00e9n\u00e9r\u00e9 par l'IA peut contenir des erreurs ou inexactitudes. Consultez toujours des professionnels qualifi\u00e9s avant de prendre des d\u00e9cisions d'achat."
      },
      "userResponsibilities": {
        "title": "3. Responsabilit\u00e9s de l'utilisateur",
        "accurate": "Fournir des informations exactes sur les biens",
        "lawful": "Utiliser la plateforme \u00e0 des fins l\u00e9gales uniquement",
        "credentials": "Garder vos identifiants de compte s\u00e9curis\u00e9s",
        "rights": "Ne t\u00e9l\u00e9verser que des documents et photos dont vous avez les droits d'utilisation"
      },
      "ip": {
        "title": "4. Propri\u00e9t\u00e9 intellectuelle",
        "userContent": "Vous conservez la propri\u00e9t\u00e9 de tout contenu que vous t\u00e9l\u00e9versez (documents, photos). En t\u00e9l\u00e9versant, vous nous accordez une licence limit\u00e9e pour traiter ce contenu afin de fournir nos services.",
        "aiContent": "Le contenu g\u00e9n\u00e9r\u00e9 par l'IA (analyses, images redesign\u00e9es) est fourni pour votre usage personnel. Vous pouvez le t\u00e9l\u00e9charger et le partager librement.",
        "platform": "La plateforme AppArt Agent, y compris son design, son code et ses fonctionnalit\u00e9s, reste notre propri\u00e9t\u00e9 intellectuelle."
      },
      "availability": {
        "title": "5. Disponibilit\u00e9 du service",
        "content": "AppArt Agent est fourni \u00ab tel quel \u00bb sans garantie. Nous ne garantissons pas une disponibilit\u00e9 ininterrompue du service. Nous pouvons effectuer des maintenances ou mises \u00e0 jour affectant temporairement l'acc\u00e8s."
      },
      "liability": {
        "title": "6. Limitation de responsabilit\u00e9",
        "content": "Dans les limites autoris\u00e9es par la loi, AppArt Agent ne saurait \u00eatre tenu responsable de tout dommage indirect, accessoire ou cons\u00e9cutif r\u00e9sultant de votre utilisation de la plateforme. Cela inclut les d\u00e9cisions prises sur la base d'analyses ou estimations g\u00e9n\u00e9r\u00e9es par l'IA."
      },
      "termination": {
        "title": "7. R\u00e9siliation de compte",
        "content": "Nous pouvons suspendre ou r\u00e9silier les comptes qui enfreignent ces conditions. Vous pouvez supprimer votre compte \u00e0 tout moment, ce qui supprimera d\u00e9finitivement toutes vos donn\u00e9es."
      },
      "law": {
        "title": "8. Droit applicable",
        "content": "Ces conditions sont r\u00e9gies par le droit fran\u00e7ais. Tout litige sera soumis \u00e0 la juridiction des tribunaux fran\u00e7ais."
      },
      "changes": {
        "title": "9. Modifications de ces conditions",
        "content": "Nous pouvons mettre \u00e0 jour ces conditions de temps en temps. L'utilisation continue de la plateforme apr\u00e8s les modifications constitue une acceptation des nouvelles conditions."
      },
      "contactEmail": "legal@appartagent.com"
    }
  },
  "cookie": {
    "title": "Pr\u00e9f\u00e9rences de cookies",
    "description": "Nous utilisons des cookies pour am\u00e9liorer votre exp\u00e9rience. Les cookies essentiels sont n\u00e9cessaires au fonctionnement du site. Les cookies analytiques nous aident \u00e0 comprendre comment vous utilisez l'application.",
    "acceptAll": "Tout accepter",
    "rejectNonEssential": "Refuser les non-essentiels",
    "managePreferences": "G\u00e9rer les pr\u00e9f\u00e9rences",
    "savePreferences": "Enregistrer les pr\u00e9f\u00e9rences",
    "essential": {
      "title": "Cookies essentiels",
      "description": "N\u00e9cessaires \u00e0 l'authentification et aux fonctionnalit\u00e9s de base. Ne peuvent pas \u00eatre d\u00e9sactiv\u00e9s."
    },
    "analytics": {
      "title": "Cookies analytiques",
      "description": "Nous aident \u00e0 comprendre comment vous utilisez l'application pour l'am\u00e9liorer. Fournis par PostHog."
    },
    "alwaysActive": "Toujours actif"
  },
  "feedback": {
    "button": "Feedback",
    "title": "Envoyer un feedback",
    "type": {
      "label": "Type",
      "bug_report": "Rapport de bug",
      "feature_request": "Demande de fonctionnalit\u00e9",
      "general_feedback": "Feedback g\u00e9n\u00e9ral"
    },
    "message": {
      "label": "Message",
      "placeholder": "D\u00e9crivez le probl\u00e8me ou la suggestion..."
    },
    "email": {
      "label": "Email (optionnel)",
      "placeholder": "votre@email.com"
    },
    "screenshot": {
      "label": "Capture d'\u00e9cran (optionnel)",
      "hint": "Glissez-d\u00e9posez ou cliquez pour t\u00e9l\u00e9verser une image (max 5 Mo)"
    },
    "submit": "Envoyer",
    "submitting": "Envoi en cours...",
    "success": "Merci ! Nous examinerons votre feedback.",
    "error": "\u00c9chec de l'envoi. Veuillez r\u00e9essayer."
  },
  "errors": {
    "notFound": {
      "title": "Page introuvable",
      "description": "La page que vous recherchez n'existe pas ou a \u00e9t\u00e9 d\u00e9plac\u00e9e.",
      "goHome": "Accueil",
      "goBack": "Retour",
      "goDashboard": "Aller au tableau de bord"
    },
    "serverError": {
      "title": "Une erreur est survenue",
      "description": "Une erreur inattendue s'est produite. Veuillez r\u00e9essayer.",
      "tryAgain": "R\u00e9essayer",
      "reportIssue": "Signaler ce probl\u00e8me",
      "details": "D\u00e9tails de l'erreur"
    }
  },
  "footer": {
    "copyright": "\u00a9 2026 AppArt Agent. Tous droits r\u00e9serv\u00e9s.",
    "tagline": "Aide \u00e0 la d\u00e9cision d'achat immobilier propuls\u00e9e par l'IA",
    "privacy": "Politique de confidentialit\u00e9",
    "terms": "CGU",
    "feedback": "Feedback"
  }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/messages/en.json frontend/messages/fr.json
git commit -m "feat: add i18n keys for legal, cookie, feedback, errors, footer"
```

---

## Task 5: Cookie Consent Banner

**Files:**

- Create: `frontend/src/components/ui/CookieConsent.tsx`
- Modify: `frontend/src/components/PostHogProvider.tsx`
- Modify: `frontend/src/app/[locale]/layout.tsx:55-74`

- [ ] **Step 1: Create the CookieConsent component**

Create `frontend/src/components/ui/CookieConsent.tsx`:

```tsx
'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { Cookie, X } from 'lucide-react'

type CookiePreferences = {
  essential: boolean
  analytics: boolean
}

const COOKIE_NAME = 'cookie_consent'
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60 // 12 months in seconds

function getCookieConsent(): CookiePreferences | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(?:^|; )${COOKIE_NAME}=([^;]*)`))
  if (!match) return null
  try {
    return JSON.parse(decodeURIComponent(match[1]))
  } catch {
    return null
  }
}

function setCookieConsent(prefs: CookiePreferences) {
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(JSON.stringify(prefs))};path=/;max-age=${COOKIE_MAX_AGE};SameSite=Lax`
  window.dispatchEvent(new CustomEvent('cookie-consent-change', { detail: prefs }))
}

export function getAnalyticsConsent(): boolean {
  const prefs = getCookieConsent()
  return prefs?.analytics ?? false
}

export default function CookieConsent() {
  const t = useTranslations('cookie')
  const [visible, setVisible] = useState(false)
  const [showPreferences, setShowPreferences] = useState(false)
  const [analyticsEnabled, setAnalyticsEnabled] = useState(false)

  useEffect(() => {
    const existing = getCookieConsent()
    if (!existing) {
      setVisible(true)
    }
  }, [])

  const handleAcceptAll = useCallback(() => {
    setCookieConsent({ essential: true, analytics: true })
    setVisible(false)
  }, [])

  const handleRejectNonEssential = useCallback(() => {
    setCookieConsent({ essential: true, analytics: false })
    setVisible(false)
  }, [])

  const handleSavePreferences = useCallback(() => {
    setCookieConsent({ essential: true, analytics: analyticsEnabled })
    setVisible(false)
  }, [analyticsEnabled])

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white border-t border-gray-200 shadow-lg">
      <div className="container mx-auto max-w-4xl">
        <div className="flex items-start gap-3">
          <Cookie className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 text-sm">{t('title')}</h3>
            <p className="text-sm text-gray-600 mt-1">{t('description')}</p>

            {showPreferences && (
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('essential.title')}</p>
                    <p className="text-xs text-gray-500">{t('essential.description')}</p>
                  </div>
                  <span className="text-xs text-gray-400 font-medium">{t('alwaysActive')}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('analytics.title')}</p>
                    <p className="text-xs text-gray-500">{t('analytics.description')}</p>
                  </div>
                  <button
                    onClick={() => setAnalyticsEnabled(!analyticsEnabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      analyticsEnabled ? 'bg-primary-600' : 'bg-gray-300'
                    }`}
                    role="switch"
                    aria-checked={analyticsEnabled}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        analyticsEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mt-4">
              {showPreferences ? (
                <button
                  onClick={handleSavePreferences}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  {t('savePreferences')}
                </button>
              ) : (
                <>
                  <button
                    onClick={handleAcceptAll}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    {t('acceptAll')}
                  </button>
                  <button
                    onClick={handleRejectNonEssential}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    {t('rejectNonEssential')}
                  </button>
                  <button
                    onClick={() => setShowPreferences(true)}
                    className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {t('managePreferences')}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update PostHogProvider to gate on cookie consent**

Replace the full contents of `frontend/src/components/PostHogProvider.tsx` with:

```tsx
'use client'

import { Suspense, useEffect, useState } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'
import { POSTHOG_KEY, POSTHOG_HOST } from '@/lib/posthog'
import { getAnalyticsConsent } from '@/components/ui/CookieConsent'

function PostHogPageView() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (!POSTHOG_KEY) return
    const url = window.origin + pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '')
    posthog.capture('$pageview', { $current_url: url })
  }, [pathname, searchParams])

  return null
}

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  const [analyticsAllowed, setAnalyticsAllowed] = useState(false)

  useEffect(() => {
    // Check initial consent
    setAnalyticsAllowed(getAnalyticsConsent())

    // Listen for consent changes
    const handleConsentChange = (e: Event) => {
      const detail = (e as CustomEvent).detail
      setAnalyticsAllowed(detail.analytics)

      if (detail.analytics && POSTHOG_KEY) {
        posthog.init(POSTHOG_KEY, {
          api_host: '/ingest',
          ui_host: POSTHOG_HOST,
          person_profiles: 'identified_only',
          capture_pageview: false,
          capture_pageleave: true,
          autocapture: true,
        })
      } else if (!detail.analytics && posthog.__loaded) {
        posthog.opt_out_capturing()
      }
    }

    window.addEventListener('cookie-consent-change', handleConsentChange)
    return () => window.removeEventListener('cookie-consent-change', handleConsentChange)
  }, [])

  // Initialize PostHog if consent was already given (returning user)
  useEffect(() => {
    if (analyticsAllowed && POSTHOG_KEY && !posthog.__loaded) {
      posthog.init(POSTHOG_KEY, {
        api_host: '/ingest',
        ui_host: POSTHOG_HOST,
        person_profiles: 'identified_only',
        capture_pageview: false,
        capture_pageleave: true,
        autocapture: true,
      })
    }
  }, [analyticsAllowed])

  if (!POSTHOG_KEY || !analyticsAllowed) {
    return <>{children}</>
  }

  return (
    <PHProvider client={posthog}>
      <Suspense fallback={null}>
        <PostHogPageView />
      </Suspense>
      {children}
    </PHProvider>
  )
}
```

- [ ] **Step 3: Mount CookieConsent in the layout**

In `frontend/src/app/[locale]/layout.tsx`, add the import at the top (after the existing imports):

```tsx
import CookieConsent from '@/components/ui/CookieConsent'
```

Then update the body content to include `CookieConsent` after `Providers`:

```tsx
        <NextIntlClientProvider messages={messages}>
          <Providers>
            {children}
            <CookieConsent />
          </Providers>
        </NextIntlClientProvider>
```

- [ ] **Step 4: Verify it compiles**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm build`
Expected: Build succeeds (or at minimum no TypeScript errors — `pnpm tsc --noEmit`)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/CookieConsent.tsx frontend/src/components/PostHogProvider.tsx frontend/src/app/[locale]/layout.tsx
git commit -m "feat: add GDPR cookie consent banner, gate PostHog on consent"
```

---

## Task 6: Shared Footer Component

**Files:**

- Create: `frontend/src/components/ui/Footer.tsx`
- Modify: `frontend/src/app/[locale]/layout.tsx`
- Modify: `frontend/src/app/[locale]/page.tsx`

- [ ] **Step 1: Create the Footer component**

Create `frontend/src/components/ui/Footer.tsx`:

```tsx
'use client'

import { useTranslations } from 'next-intl'
import Link from 'next/link'

export default function Footer() {
  const t = useTranslations('footer')

  return (
    <footer className="bg-gray-900 text-white py-8 mt-auto">
      <div className="container mx-auto px-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <p className="text-sm">{t('copyright')}</p>
            <p className="text-gray-400 text-xs mt-1">{t('tagline')}</p>
          </div>
          <nav className="flex items-center gap-4 text-sm text-gray-400">
            <Link href="/legal/privacy" className="hover:text-white transition-colors">
              {t('privacy')}
            </Link>
            <Link href="/legal/terms" className="hover:text-white transition-colors">
              {t('terms')}
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  )
}
```

- [ ] **Step 2: Add Footer to the layout**

In `frontend/src/app/[locale]/layout.tsx`, add the import:

```tsx
import Footer from '@/components/ui/Footer'
```

Update the body to include the Footer and a flex layout so the footer sticks to the bottom:

```tsx
      <body className={`${inter.className} flex flex-col min-h-screen`}>
        <NextIntlClientProvider messages={messages}>
          <Providers>
            <div className="flex-1">
              {children}
            </div>
            <Footer />
            <CookieConsent />
          </Providers>
        </NextIntlClientProvider>
      </body>
```

- [ ] **Step 3: Remove inline footer from landing page**

In `frontend/src/app/[locale]/page.tsx`, find and remove the inline footer section (the `<footer>` element with `bg-gray-900`). This is the block that looks like:

```tsx
      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p>{t('footer.copyright')}</p>
          <p className="text-gray-400 mt-2">{t('footer.tagline')}</p>
        </div>
      </footer>
```

Remove that entire block. The shared Footer in the layout now handles this.

- [ ] **Step 4: Verify it compiles**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/Footer.tsx frontend/src/app/[locale]/layout.tsx frontend/src/app/[locale]/page.tsx
git commit -m "feat: add shared footer with legal links to all pages"
```

---

## Task 7: Legal Pages (Privacy Policy & Terms of Service)

**Files:**

- Create: `frontend/src/app/[locale]/legal/privacy/page.tsx`
- Create: `frontend/src/app/[locale]/legal/terms/page.tsx`

- [ ] **Step 1: Create the Privacy Policy page**

Create `frontend/src/app/[locale]/legal/privacy/page.tsx`:

```tsx
import { useTranslations } from 'next-intl'
import { getTranslations } from 'next-intl/server'
import { Shield } from 'lucide-react'
import type { Metadata } from 'next'

type Props = { params: Promise<{ locale: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'legal.privacy' })
  return { title: t('title') }
}

export default function PrivacyPolicyPage() {
  const t = useTranslations('legal.privacy')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
        </div>
        <p className="text-sm text-gray-500 mb-8">{t('lastUpdated')}</p>

        <div className="prose prose-gray max-w-none space-y-8">
          <p>{t('intro')}</p>

          <section>
            <h2>{t('controller.title')}</h2>
            <p>{t('controller.content')}</p>
          </section>

          <section>
            <h2>{t('dataCollected.title')}</h2>
            <ul>
              <li>{t('dataCollected.account')}</li>
              <li>{t('dataCollected.property')}</li>
              <li>{t('dataCollected.documents')}</li>
              <li>{t('dataCollected.photos')}</li>
              <li>{t('dataCollected.generated')}</li>
              <li>{t('dataCollected.usage')}</li>
              <li>{t('dataCollected.technical')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('purpose.title')}</h2>
            <ul>
              <li>{t('purpose.analysis')}</li>
              <li>{t('purpose.price')}</li>
              <li>{t('purpose.redesign')}</li>
              <li>{t('purpose.account')}</li>
              <li>{t('purpose.improvement')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('ai.title')}</h2>
            <p>{t('ai.content')}</p>
          </section>

          <section>
            <h2>{t('storage.title')}</h2>
            <ul>
              <li>{t('storage.structured')}</li>
              <li>{t('storage.files')}</li>
              <li>{t('storage.location')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('cookies.title')}</h2>
            <ul>
              <li>{t('cookies.essential')}</li>
              <li>{t('cookies.analytics')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('retention.title')}</h2>
            <p>{t('retention.content')}</p>
          </section>

          <section>
            <h2>{t('rights.title')}</h2>
            <p>{t('rights.content')}</p>
            <ul>
              <li>{t('rights.access')}</li>
              <li>{t('rights.rectification')}</li>
              <li>{t('rights.erasure')}</li>
              <li>{t('rights.portability')}</li>
              <li>{t('rights.objection')}</li>
            </ul>
            <p>{t('rights.contact')} <a href={`mailto:${t('contactEmail')}`} className="text-primary-600 hover:underline">{t('contactEmail')}</a></p>
          </section>

          <section>
            <h2>{t('thirdParty.title')}</h2>
            <p>{t('thirdParty.content')}</p>
            <ul>
              <li>{t('thirdParty.gcp')}</li>
              <li>{t('thirdParty.gemini')}</li>
              <li>{t('thirdParty.posthog')}</li>
              <li>{t('thirdParty.resend')}</li>
              <li>{t('thirdParty.betterAuth')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('changes.title')}</h2>
            <p>{t('changes.content')}</p>
          </section>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create the Terms of Service page**

Create `frontend/src/app/[locale]/legal/terms/page.tsx`:

```tsx
import { useTranslations } from 'next-intl'
import { getTranslations } from 'next-intl/server'
import { FileText } from 'lucide-react'
import type { Metadata } from 'next'

type Props = { params: Promise<{ locale: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'legal.terms' })
  return { title: t('title') }
}

export default function TermsOfServicePage() {
  const t = useTranslations('legal.terms')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <div className="flex items-center gap-3 mb-2">
          <FileText className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
        </div>
        <p className="text-sm text-gray-500 mb-8">{t('lastUpdated')}</p>

        <div className="prose prose-gray max-w-none space-y-8">
          <p>{t('intro')}</p>

          <section>
            <h2>{t('service.title')}</h2>
            <p>{t('service.content')}</p>
          </section>

          <section>
            <h2>{t('aiDisclaimer.title')}</h2>
            <p>{t('aiDisclaimer.content')}</p>
          </section>

          <section>
            <h2>{t('userResponsibilities.title')}</h2>
            <ul>
              <li>{t('userResponsibilities.accurate')}</li>
              <li>{t('userResponsibilities.lawful')}</li>
              <li>{t('userResponsibilities.credentials')}</li>
              <li>{t('userResponsibilities.rights')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('ip.title')}</h2>
            <p>{t('ip.userContent')}</p>
            <p>{t('ip.aiContent')}</p>
            <p>{t('ip.platform')}</p>
          </section>

          <section>
            <h2>{t('availability.title')}</h2>
            <p>{t('availability.content')}</p>
          </section>

          <section>
            <h2>{t('liability.title')}</h2>
            <p>{t('liability.content')}</p>
          </section>

          <section>
            <h2>{t('termination.title')}</h2>
            <p>{t('termination.content')}</p>
          </section>

          <section>
            <h2>{t('law.title')}</h2>
            <p>{t('law.content')}</p>
          </section>

          <section>
            <h2>{t('changes.title')}</h2>
            <p>{t('changes.content')}</p>
          </section>

          <p className="text-sm text-gray-500 mt-8">
            Contact: <a href={`mailto:${t('contactEmail')}`} className="text-primary-600 hover:underline">{t('contactEmail')}</a>
          </p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Verify pages compile**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/[locale]/legal/
git commit -m "feat: add privacy policy and terms of service pages"
```

---

## Task 8: Error Pages (404 and 500)

**Files:**

- Create: `frontend/src/app/not-found.tsx`
- Create: `frontend/src/app/[locale]/error.tsx`

- [ ] **Step 1: Create the 404 page**

Create `frontend/src/app/not-found.tsx`:

```tsx
import Link from 'next/link'
import { SearchX } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <SearchX className="w-16 h-16 text-gray-400 mx-auto mb-6" />
        <h1 className="text-4xl font-bold text-gray-900 mb-2">404</h1>
        <p className="text-lg text-gray-600 mb-8">
          This page doesn&apos;t exist or has been moved.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="px-6 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go Home
          </Link>
        </div>
      </div>
    </div>
  )
}
```

Note: The root `not-found.tsx` cannot use `next-intl` hooks (it's outside the `[locale]` layout). We keep it simple with hardcoded English since it's a rare edge case.

- [ ] **Step 2: Create the 500 error boundary**

Create `frontend/src/app/[locale]/error.tsx`:

```tsx
'use client'

import { useTranslations } from 'next-intl'
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations('errors.serverError')
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-16 h-16 text-danger-500 mx-auto mb-6" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('title')}</h1>
        <p className="text-gray-600 mb-8">{t('description')}</p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
          <button
            onClick={reset}
            className="px-6 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            {t('tryAgain')}
          </button>
        </div>

        {error.message && (
          <div className="text-left">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors mx-auto"
            >
              {t('details')}
              {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showDetails && (
              <pre className="mt-2 p-3 bg-gray-100 rounded-lg text-xs text-gray-600 overflow-auto max-h-32">
                {error.message}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Verify it compiles**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/not-found.tsx frontend/src/app/[locale]/error.tsx
git commit -m "feat: add custom 404 and 500 error pages"
```

---

## Task 9: Feedback UI (Button + Modal)

**Files:**

- Create: `frontend/src/components/ui/FeedbackButton.tsx`
- Create: `frontend/src/components/ui/FeedbackModal.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/app/[locale]/layout.tsx`

- [ ] **Step 1: Add feedbackAPI to the API client**

In `frontend/src/lib/api.ts`, add after the `photosAPI` object (before the default export):

```typescript
// Feedback API
export const feedbackAPI = {
  submit: async (data: {
    type: string
    message: string
    email?: string
    screenshot?: File
  }) => {
    const formData = new FormData()
    formData.append('type', data.type)
    formData.append('message', data.message)
    if (data.email) formData.append('email', data.email)
    if (data.screenshot) formData.append('screenshot', data.screenshot)

    const response = await api.post('/api/feedback', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
}
```

- [ ] **Step 2: Create the FeedbackModal component**

Create `frontend/src/components/ui/FeedbackModal.tsx`:

```tsx
'use client'

import { useState, useRef } from 'react'
import { useTranslations } from 'next-intl'
import { X, Upload, CheckCircle } from 'lucide-react'
import { feedbackAPI } from '@/lib/api'

type FeedbackType = 'bug_report' | 'feature_request' | 'general_feedback'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  defaultType?: FeedbackType
}

export default function FeedbackModal({ isOpen, onClose, defaultType }: FeedbackModalProps) {
  const t = useTranslations('feedback')
  const [type, setType] = useState<FeedbackType>(defaultType ?? 'general_feedback')
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [screenshot, setScreenshot] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(false)

    try {
      await feedbackAPI.submit({
        type,
        message,
        email: email || undefined,
        screenshot: screenshot ?? undefined,
      })
      setSuccess(true)
      setTimeout(() => {
        onClose()
        // Reset form
        setType('general_feedback')
        setMessage('')
        setEmail('')
        setScreenshot(null)
        setSuccess(false)
      }, 2000)
    } catch {
      setError(true)
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.size <= 5 * 1024 * 1024) {
      setScreenshot(file)
    }
  }

  const types: FeedbackType[] = ['bug_report', 'feature_request', 'general_feedback']

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-t-xl sm:rounded-xl shadow-xl w-full sm:max-w-md max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{t('title')}</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {success ? (
          <div className="p-8 text-center">
            <CheckCircle className="w-12 h-12 text-success-500 mx-auto mb-3" />
            <p className="text-gray-700">{t('success')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('type.label')}</label>
              <div className="flex gap-2">
                {types.map((feedbackType) => (
                  <button
                    key={feedbackType}
                    type="button"
                    onClick={() => setType(feedbackType)}
                    className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                      type === feedbackType
                        ? 'bg-primary-50 border-primary-300 text-primary-700'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {t(`type.${feedbackType}`)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('message.label')}</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={t('message.placeholder')}
                rows={4}
                required
                minLength={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('email.label')}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('email.placeholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('screenshot.label')}</label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 px-3 py-3 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors"
              >
                <Upload className="w-4 h-4" />
                {screenshot ? screenshot.name : t('screenshot.hint')}
              </button>
            </div>

            {error && (
              <p className="text-sm text-danger-600">{t('error')}</p>
            )}

            <button
              type="submit"
              disabled={submitting || message.length < 10}
              className="w-full px-4 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? t('submitting') : t('submit')}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create the FeedbackButton component**

Create `frontend/src/components/ui/FeedbackButton.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { MessageSquarePlus } from 'lucide-react'
import FeedbackModal from './FeedbackModal'

export default function FeedbackButton() {
  const t = useTranslations('feedback')
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-full shadow-lg hover:bg-primary-700 transition-all hover:shadow-xl"
        aria-label={t('button')}
      >
        <MessageSquarePlus className="w-4 h-4" />
        <span className="hidden sm:inline">{t('button')}</span>
      </button>
      <FeedbackModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  )
}
```

- [ ] **Step 4: Mount FeedbackButton in the layout**

In `frontend/src/app/[locale]/layout.tsx`, add the import:

```tsx
import FeedbackButton from '@/components/ui/FeedbackButton'
```

Add `<FeedbackButton />` in the body, after `<Footer />` and before `<CookieConsent />`:

```tsx
            <Footer />
            <FeedbackButton />
            <CookieConsent />
```

- [ ] **Step 5: Verify it compiles**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm tsc --noEmit`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/FeedbackButton.tsx frontend/src/components/ui/FeedbackModal.tsx frontend/src/lib/api.ts frontend/src/app/[locale]/layout.tsx
git commit -m "feat: add floating feedback button with modal and API integration"
```

---

## Task 10: Final Integration Verification

**Files:** None (verification only)

- [ ] **Step 1: Run backend tests**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv run pytest backend/tests/ -v`
Expected: All tests pass (including new email and feedback tests)

- [ ] **Step 2: Run frontend type check**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm tsc --noEmit`
Expected: No TypeScript errors

- [ ] **Step 3: Run frontend lint**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent/frontend && pnpm lint`
Expected: No lint errors (or only pre-existing ones)

- [ ] **Step 4: Run backend lint**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && uv run ruff check backend/`
Expected: No lint errors

- [ ] **Step 5: Run pre-commit on all changed files**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && pre-commit run --all-files`
Expected: All checks pass

- [ ] **Step 6: Verify Docker Compose builds**

Run: `cd /Users/karaoglanbenjamin/AppArtAgent && docker compose build backend frontend`
Expected: Both images build successfully

- [ ] **Step 7: Manual smoke test checklist**

Start the app with `./dev.sh start` and verify:

- [ ] Landing page shows footer with Privacy Policy and Terms links
- [ ] Cookie consent banner appears on first visit
- [ ] Clicking "Reject Non-Essential" hides banner and prevents PostHog from loading
- [ ] Privacy Policy page renders at `/fr/legal/privacy` and `/en/legal/privacy`
- [ ] Terms of Service page renders at `/fr/legal/terms` and `/en/legal/terms`
- [ ] Visiting a non-existent URL shows the 404 page
- [ ] Feedback button visible in bottom-right corner
- [ ] Clicking feedback button opens the modal
- [ ] Submitting feedback sends request to backend (check backend logs)
- [ ] Dashboard pages also show footer
