# Sub-Project 1: Trust & Safety

**Date:** 2026-04-02
**Status:** Approved
**Scope:** Legal pages, cookie consent, error pages, feedback system, email service, footer

## Context

AppArt Agent is preparing for a public LinkedIn launch targeting French apartment buyers and the tech community. The app is deployed and functional but lacks trust and safety fundamentals required before inviting real users to store property data. This sub-project addresses those gaps.

## Goals

- Meet GDPR compliance requirements for a French-facing app
- Ensure users are never stuck on raw error screens
- Provide a low-friction channel for bug reports and feedback
- Establish an email sending service reusable for future notifications

## Non-Goals

- User account management (Sub-Project 2)
- Email notifications beyond feedback delivery (Sub-Project 7)
- Help center or documentation (Sub-Project 8)

---

## 1. Legal Pages

### Routes

- `/[locale]/legal/privacy` — Privacy policy
- `/[locale]/legal/terms` — Terms of service

### Requirements

- Full French and English translations via next-intl
- Accessible from footer on every page (landing + authenticated)
- Static content pages using the app layout (header + footer)
- No authentication required (public pages)

### Privacy Policy Content Coverage

- Identity of the data controller (AppArt Agent)
- Data collected: user account info (name, email), property details (address, price, surface area), uploaded documents (PDFs, images), uploaded photos, AI-generated analyses and redesigns
- Purpose of processing: property analysis, document analysis, price estimation, interior redesign generation
- AI processing disclosure: documents and photos are sent to Google Gemini (Vertex AI) for analysis and generation
- Storage: Google Cloud Storage (documents, photos), Cloud SQL PostgreSQL (structured data)
- Cookies: essential (session), analytics (PostHog — opt-in only)
- Data retention: data kept as long as account is active, deleted on account deletion
- User rights under GDPR: access, rectification, erasure, portability, objection
- Contact information for exercising rights
- Third-party services: Google Cloud Platform, Google Gemini/Vertex AI, PostHog, Resend, Better Auth

### Terms of Service Content Coverage

- Service description: AI-powered apartment purchasing decision platform
- User responsibilities: accurate data, lawful use
- AI disclaimer: analyses are informational, not professional legal/financial advice
- Intellectual property: user retains ownership of uploaded content, AI-generated content license
- Service availability: no uptime guarantee (beta/early stage)
- Limitation of liability
- Account termination conditions
- Governing law: French law
- Modification clause: terms may be updated with notice

---

## 2. Cookie Consent Banner

### Component

- `frontend/src/components/ui/CookieConsent.tsx`
- Mounted in root layout (`frontend/src/app/[locale]/layout.tsx`)

### Behavior

- Shown as a bottom-of-screen banner on first visit (no consent cookie present)
- Three action buttons: **Accept All** / **Reject Non-Essential** / **Manage Preferences**
- "Manage Preferences" expands to show cookie categories with toggles
- Two categories:
  - **Essential** (always on, non-toggleable): session cookies, auth cookies, cookie consent cookie
  - **Analytics** (opt-in, default off): PostHog tracking
- Consent stored in `cookie_consent` cookie (client-side JSON: `{"essential": true, "analytics": false}`)
- Cookie expiry: 12 months
- Banner reappears if consent cookie is cleared or expired

### PostHog Integration

- PostHog initialization in `Providers.tsx` must be gated on analytics consent
- Check `cookie_consent` cookie on app load
- If analytics consent is `true`: initialize PostHog normally
- If analytics consent is `false` or absent: do not initialize PostHog, do not send any events
- When user changes consent: reinitialize or disable PostHog accordingly without page reload

### i18n

- All banner text (title, description, button labels, category names) translated FR/EN

---

## 3. Error Pages

### 404 — Not Found

- File: `frontend/src/app/not-found.tsx` (App Router convention)
- Content: friendly message ("This page doesn't exist"), Lucide icon, two buttons:
  - "Go to Dashboard" (if authenticated) / "Go Home" (if not)
  - "Go Back" (browser history)
- Uses app styling (Tailwind, semantic tokens)
- Translated via next-intl

### 500 — Runtime Error

- File: `frontend/src/app/error.tsx` (App Router error boundary)
- Content: "Something went wrong" message, Lucide icon, two actions:
  - "Try Again" button (calls `reset()` from error boundary)
  - "Report this issue" link that opens the feedback modal
- Includes `error.message` in a collapsible "Details" section (dev info)
- Uses app styling
- Translated via next-intl

---

## 4. Feedback System

### Frontend

#### Floating Button

- Persistent floating button in bottom-right corner of the app
- Label: "Feedback" with a Lucide icon (e.g., `MessageSquarePlus`)
- Visible on all authenticated pages
- Also visible on landing page (for visitors who haven't signed up)
- Z-index above other content but below modals

#### Feedback Modal

- Opens on button click
- Fields:
  - **Type** (required): Radio/select — "Bug Report" / "Feature Request" / "General Feedback"
  - **Message** (required): Textarea, min 10 characters
  - **Screenshot** (optional): File upload (image only, max 5MB), with drag-and-drop support
  - **Email** (optional, pre-filled if authenticated): For follow-up contact
- Submit button with loading state
- Success state: "Thank you! We'll review your feedback." with auto-close after 3 seconds
- Error state: "Failed to send. Please try again." with retry option

#### Error Page Integration

- 500 error page "Report this issue" link opens the feedback modal with type pre-set to "Bug Report"

### Backend

#### Endpoint

`POST /api/feedback`

- No authentication required (allow anonymous feedback from landing page visitors)
- Rate limited: max 5 submissions per IP per hour

#### Request Body

```json
{
  "type": "bug_report" | "feature_request" | "general_feedback",
  "message": "string (required, min 10 chars)",
  "email": "string (optional)",
  "screenshot": "file (optional, image/*, max 5MB)"
}
```

#### Processing

1. If screenshot provided: upload to storage (GCS/MinIO) in a `feedback/` prefix
2. Send structured email via Resend to feedback address
3. Return 200 with success message

#### Email Format

- **To:** configured feedback email address (env var: `FEEDBACK_EMAIL`)
- **From:** `noreply@appartagent.com` (verified Resend domain)
- **Subject:** `[AppArt Agent] {type}: {first 50 chars of message}`
- **Body:** HTML email with:
  - Type badge
  - Full message text
  - User email (if provided)
  - User ID and name (if authenticated)
  - Screenshot attachment or link (if provided)
  - Timestamp
  - Browser/device info (user agent)

---

## 5. Email Service (Resend)

### Service

- File: `backend/app/services/email.py`
- Wraps Resend Python SDK (`resend` package)
- Async-compatible
- Single function initially: `send_email(to, subject, html_body, attachments=None)`
- Designed for reuse in Sub-Project 7 (email notifications)

### Configuration

- Env var: `RESEND_API_KEY` — Resend API key
- Env var: `FEEDBACK_EMAIL` — destination for feedback emails
- Env var: `EMAIL_FROM` — sender address (default: `noreply@appartagent.com`)
- Added to `backend/app/core/config.py` (Pydantic settings)
- Added to `.env.example`

### Setup Requirements

- Resend account created
- Domain `appartagent.com` verified in Resend
- DNS records: DKIM, SPF, DMARC configured

### Error Handling

- Email send failure should not break the feedback endpoint
- Log errors, return success to user (feedback is best-effort delivery)
- Resend has built-in retry logic

---

## 6. Footer Update

### Current State

- Landing page has a footer
- Authenticated pages (dashboard, properties, etc.) do not have a consistent footer

### Changes

- Create a shared `Footer` component (`frontend/src/components/ui/Footer.tsx`)
- Include in the app layout so it appears on all pages
- Footer content:
  - Links: Privacy Policy, Terms of Service
  - Feedback button (or link that opens feedback modal)
  - Copyright: "(c) 2026 AppArt Agent"
- Responsive: single row on desktop, stacked on mobile
- Translated FR/EN

---

## Technical Summary

### New Dependencies

- `resend` (Python package) — email sending
- No new frontend dependencies

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/components/ui/CookieConsent.tsx` | Cookie consent banner component |
| `frontend/src/components/ui/FeedbackModal.tsx` | Feedback form modal |
| `frontend/src/components/ui/FeedbackButton.tsx` | Floating feedback trigger button |
| `frontend/src/components/ui/Footer.tsx` | Shared footer component |
| `frontend/src/app/not-found.tsx` | Custom 404 page |
| `frontend/src/app/error.tsx` | Custom 500 error page |
| `frontend/src/app/[locale]/legal/privacy/page.tsx` | Privacy policy page |
| `frontend/src/app/[locale]/legal/terms/page.tsx` | Terms of service page |
| `frontend/messages/fr.json` (updates) | French translations for new content |
| `frontend/messages/en.json` (updates) | English translations for new content |
| `backend/app/services/email.py` | Resend email service |
| `backend/app/api/feedback.py` | Feedback API endpoint |

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/app/[locale]/layout.tsx` | Add Footer, mount CookieConsent |
| `frontend/src/components/Providers.tsx` | Gate PostHog on cookie consent |
| `backend/app/main.py` | Register feedback router |
| `backend/app/core/config.py` | Add Resend/email env vars |
| `backend/pyproject.toml` | Add `resend` dependency |
| `.env.example` | Add `RESEND_API_KEY`, `FEEDBACK_EMAIL`, `EMAIL_FROM` |

### No Database Changes

No new models, no migrations. Feedback is email-only, cookie consent is client-side.
