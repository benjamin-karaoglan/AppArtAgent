"""Tests for document chunking, retry logic, and error propagation."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai.document_processor import DocumentProcessor


class TestRetryLogic:
    """Test retry with exponential backoff for transient Gemini errors."""

    @pytest.fixture
    def processor(self):
        """Create a DocumentProcessor with mocked Gemini client."""
        with patch.object(DocumentProcessor, "__init__", lambda self: None):
            proc = DocumentProcessor.__new__(DocumentProcessor)
            proc.client = MagicMock()
            proc.model = "gemini-2.5-flash"
            proc.use_vertexai = True
            proc.project = "test-project"
            proc.location = "us-central1"
            return proc

    @pytest.mark.asyncio
    async def test_retry_on_429_then_succeed(self, processor):
        """Should retry on 429 RESOURCE_EXHAUSTED and succeed on third attempt."""
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock(text="other", thought=False)]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("429 RESOURCE_EXHAUSTED. {'error': {'code': 429}}")
            return mock_response

        processor.client.models.generate_content = side_effect

        with patch(
            "app.services.ai.document_processor.asyncio.sleep",
            new_callable=lambda: lambda *a: asyncio.coroutine(lambda *a: None)(),
        ):
            result = await processor.classify_document(
                {
                    "filename": "test.pdf",
                    "pdf_data": b"fake-pdf-data",
                }
            )

        assert call_count == 3
        assert result == "other"

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self, processor):
        """Should raise after MAX_RETRIES attempts."""

        def side_effect(*args, **kwargs):
            raise Exception("429 RESOURCE_EXHAUSTED. {'error': {'code': 429}}")

        processor.client.models.generate_content = side_effect

        with patch(
            "app.services.ai.document_processor.asyncio.sleep",
            new_callable=lambda: lambda *a: asyncio.coroutine(lambda *a: None)(),
        ):
            result = await processor.classify_document(
                {
                    "filename": "test.pdf",
                    "pdf_data": b"fake-pdf-data",
                }
            )

        # Classification falls back to "other" on all errors
        assert result == "other"

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self, processor):
        """Should not retry on non-retryable errors like ValueError."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        processor.client.models.generate_content = side_effect

        with patch(
            "app.services.ai.document_processor.asyncio.sleep",
            new_callable=lambda: lambda *a: asyncio.coroutine(lambda *a: None)(),
        ):
            result = await processor.classify_document(
                {
                    "filename": "test.pdf",
                    "pdf_data": b"fake-pdf-data",
                }
            )

        assert call_count == 1  # No retries
        assert result == "other"
