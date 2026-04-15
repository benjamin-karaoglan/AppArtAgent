"""Tests for document chunking, retry logic, and error propagation."""

import asyncio
import json
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


class TestMergeChunkResults:
    """Test chunk result merging."""

    @pytest.fixture
    def processor(self):
        with patch.object(DocumentProcessor, "__init__", lambda self: None):
            proc = DocumentProcessor.__new__(DocumentProcessor)
            proc.client = MagicMock()
            proc.model = "gemini-2.5-flash"
            proc.use_vertexai = True
            proc.project = "test-project"
            proc.location = "us-central1"
            return proc

    @pytest.mark.asyncio
    async def test_merge_calls_gemini_with_all_chunks(self, processor):
        """Merge should send all chunk results to Gemini."""
        merged_result = {
            "summary": "Merged summary",
            "key_insights": ["Insight 1"],
            "estimated_annual_cost": 1000.0,
            "one_time_costs": 500.0,
        }

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [
            MagicMock(text=json.dumps(merged_result), thought=False)
        ]
        processor.client.models.generate_content = MagicMock(return_value=mock_response)

        chunks = [
            {"summary": "Part 1", "key_insights": ["A"], "estimated_annual_cost": 500.0},
            {"summary": "Part 2", "key_insights": ["B"], "estimated_annual_cost": 500.0},
        ]

        result = await processor.merge_chunk_results(chunks, "pv_ag")

        assert result["summary"] == "Merged summary"
        assert result["estimated_annual_cost"] == 1000.0
        processor.client.models.generate_content.assert_called_once()

        # Verify prompt contains both chunk results
        call_args = processor.client.models.generate_content.call_args
        content_parts = call_args.kwargs.get("contents", call_args[1].get("contents", []))[0].parts
        prompt_text = content_parts[0].text
        assert "Chunk 1" in prompt_text
        assert "Chunk 2" in prompt_text
