"""Tests for the email service."""

from unittest.mock import patch

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
