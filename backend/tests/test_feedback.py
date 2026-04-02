"""Tests for the feedback API endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestFeedbackEndpoint:
    """Test POST /api/feedback."""

    @patch("app.api.feedback.settings")
    @patch("app.api.feedback.send_email")
    def test_submit_feedback_success(self, mock_send_email, mock_settings):
        mock_send_email.return_value = True
        mock_settings.FEEDBACK_EMAIL = "feedback@example.com"

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
        call_kwargs = mock_send_email.call_args.kwargs
        assert (
            "bug" in call_kwargs["subject"].lower() and "report" in call_kwargs["subject"].lower()
        )

    @patch("app.api.feedback.settings")
    @patch("app.api.feedback.send_email")
    def test_submit_feedback_with_email(self, mock_send_email, mock_settings):
        mock_send_email.return_value = True
        mock_settings.FEEDBACK_EMAIL = "feedback@example.com"

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

    @patch("app.api.feedback.settings")
    @patch("app.api.feedback.send_email")
    def test_submit_feedback_email_failure_still_returns_ok(self, mock_send_email, mock_settings):
        """Feedback submission should succeed even if email delivery fails."""
        mock_send_email.return_value = False
        mock_settings.FEEDBACK_EMAIL = "feedback@example.com"

        response = client.post(
            "/api/feedback",
            data={
                "type": "general_feedback",
                "message": "Great app, love the price analysis feature!",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"
