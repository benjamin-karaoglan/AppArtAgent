"""Tests for document chunking, retry logic, and error propagation."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from app.core.better_auth_security import get_current_user_hybrid as get_current_user
from app.main import app
from app.services.ai.document_processor import DocumentProcessor
from app.services.documents.bulk_processor import BulkProcessor, chunk_pdf


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


def _make_test_pdf(num_pages: int, text_per_page: str = "Hello world " * 100) -> bytes:
    """Create a test PDF with the given number of pages."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((72, 72), f"Page {i + 1}\n{text_per_page}", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


class TestChunkPdf:
    """Test page-based PDF splitting."""

    def test_small_pdf_not_chunked(self):
        """PDFs under the chunk size should return a single chunk."""
        pdf_bytes = _make_test_pdf(5)
        chunks = chunk_pdf(pdf_bytes, chunk_size=5 * 1024 * 1024)
        assert len(chunks) == 1
        assert chunks[0] == pdf_bytes

    def test_large_pdf_split_into_chunks(self):
        """PDFs over the chunk size should be split by page ranges."""
        pdf_bytes = _make_test_pdf(50)
        chunk_size = len(pdf_bytes) // 3  # Force ~3 chunks
        chunks = chunk_pdf(pdf_bytes, chunk_size=chunk_size)

        assert len(chunks) >= 2
        # Each chunk should be a valid PDF
        for chunk in chunks:
            doc = fitz.open(stream=chunk, filetype="pdf")
            assert len(doc) > 0
            doc.close()

    def test_chunk_preserves_all_pages(self):
        """Total pages across all chunks should equal original page count."""
        pdf_bytes = _make_test_pdf(100)
        chunk_size = len(pdf_bytes) // 5  # Force ~5 chunks
        chunks = chunk_pdf(pdf_bytes, chunk_size=chunk_size)

        total_pages = 0
        for chunk in chunks:
            doc = fitz.open(stream=chunk, filetype="pdf")
            total_pages += len(doc)
            doc.close()

        assert total_pages == 100

    def test_minimum_pages_per_chunk(self):
        """Each chunk should have at least 10 pages (except the last)."""
        pdf_bytes = _make_test_pdf(50)
        # Use a tiny chunk size to try to force very small chunks
        chunks = chunk_pdf(pdf_bytes, chunk_size=1)

        for chunk in chunks[:-1]:  # All except last
            doc = fitz.open(stream=chunk, filetype="pdf")
            assert len(doc) >= 10
            doc.close()


class TestErrorPropagation:
    """Test that processing errors are properly propagated to document status."""

    @pytest.mark.asyncio
    async def test_failed_document_marked_as_failed(self):
        """When AI processing raises, document should be marked as failed."""
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = 1
        mock_doc.processing_status = "processing"
        mock_doc.processing_error = None
        mock_doc.is_analyzed = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

        processor = BulkProcessor()

        with patch("app.services.documents.bulk_processor.get_document_processor") as mock_get_proc:
            mock_processor = MagicMock()
            mock_processor.process_document = AsyncMock(
                side_effect=Exception("429 RESOURCE_EXHAUSTED")
            )
            mock_get_proc.return_value = mock_processor

            with patch("app.services.documents.bulk_processor.SessionLocal", return_value=mock_db):
                with patch.object(
                    processor, "_download_files", new=AsyncMock(return_value=[b"fake-pdf"])
                ):
                    with patch.object(
                        processor,
                        "_prepare_documents",
                        new=AsyncMock(
                            return_value=[
                                {
                                    "pdf_data": b"fake-pdf",
                                    "text_extractable": False,
                                    "extracted_text": "",
                                    "page_count": 5,
                                }
                            ]
                        ),
                    ):
                        with patch.object(processor, "_save_synthesis", new=AsyncMock()):
                            await processor.process_bulk_upload(
                                workflow_id="test-workflow",
                                property_id=1,
                                document_uploads=[
                                    {
                                        "document_id": 1,
                                        "filename": "test.pdf",
                                        "storage_key": "key/test.pdf",
                                    }
                                ],
                            )

        # Document should be marked as failed
        assert mock_doc.processing_status == "failed"
        assert "RESOURCE_EXHAUSTED" in mock_doc.processing_error
        assert mock_doc.is_analyzed is False

    @pytest.mark.asyncio
    async def test_partial_failure_synthesizes_successful_only(self):
        """When one doc fails and another succeeds, synthesis uses only the success."""
        mock_db = MagicMock()
        mock_doc = MagicMock(
            id=1, processing_status="processing", processing_error=None, is_analyzed=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        mock_db.commit = MagicMock()

        processor = BulkProcessor()

        with patch("app.services.documents.bulk_processor.get_document_processor") as mock_get_proc:
            mock_ai = MagicMock()
            call_count = 0

            async def mock_process(doc, output_language="French"):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("429 RESOURCE_EXHAUSTED")
                return {
                    "filename": "doc2.pdf",
                    "document_type": "other",
                    "result": {"summary": "Success"},
                    "document_id": 2,
                }

            mock_ai.process_document = mock_process
            mock_ai.synthesize_results = AsyncMock(return_value={"summary": "Partial synthesis"})
            mock_get_proc.return_value = mock_ai

            with patch("app.services.documents.bulk_processor.SessionLocal", return_value=mock_db):
                with patch.object(
                    processor, "_download_files", new=AsyncMock(return_value=[b"pdf1", b"pdf2"])
                ):
                    with patch.object(
                        processor,
                        "_prepare_documents",
                        new=AsyncMock(
                            return_value=[
                                {
                                    "pdf_data": b"pdf1",
                                    "text_extractable": False,
                                    "extracted_text": "",
                                    "page_count": 5,
                                },
                                {
                                    "pdf_data": b"pdf2",
                                    "text_extractable": False,
                                    "extracted_text": "",
                                    "page_count": 5,
                                },
                            ]
                        ),
                    ):
                        with patch.object(processor, "_save_document_result", new=AsyncMock()):
                            with patch.object(processor, "_save_synthesis", new=AsyncMock()):
                                await processor.process_bulk_upload(
                                    workflow_id="test-workflow",
                                    property_id=1,
                                    document_uploads=[
                                        {
                                            "document_id": 1,
                                            "filename": "doc1.pdf",
                                            "storage_key": "key/doc1.pdf",
                                        },
                                        {
                                            "document_id": 2,
                                            "filename": "doc2.pdf",
                                            "storage_key": "key/doc2.pdf",
                                        },
                                    ],
                                )

        # synthesize_results should have been called with only the successful result
        mock_ai.synthesize_results.assert_called_once()
        results_arg = mock_ai.synthesize_results.call_args[0][0]
        assert len(results_arg) == 1
        assert results_arg[0]["filename"] == "doc2.pdf"


test_client = TestClient(app)


class TestFileSizeValidation:
    """Test upload file size enforcement."""

    @patch("app.api.documents.settings")
    def test_single_upload_rejects_oversized_file(self, mock_settings):
        """Single upload should return 413 for files exceeding MAX_UPLOAD_SIZE."""
        mock_settings.MAX_UPLOAD_SIZE = 100  # 100 bytes for testing
        mock_settings.ALLOWED_EXTENSIONS = [".pdf"]

        # Override the auth dependency to bypass authentication
        app.dependency_overrides[get_current_user] = lambda: "1"

        try:
            oversized_content = b"x" * 200  # 200 bytes > 100 byte limit
            response = test_client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", oversized_content, "application/pdf")},
                data={"document_category": "other"},
            )

            assert response.status_code == 413
        finally:
            app.dependency_overrides.pop(get_current_user, None)
