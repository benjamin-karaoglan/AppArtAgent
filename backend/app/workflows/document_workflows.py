"""
Temporal workflows for document processing.
Workflows orchestrate activities and define the processing logic.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Dict, Any, List
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from app.workflows.activities import (
        download_from_minio,
        pdf_to_images,
        analyze_with_langchain,
        update_document_status,
        save_analysis_results,
        calculate_file_hash,
        run_langgraph_agent,
        save_document_synthesis,
    )

logger = logging.getLogger(__name__)


@workflow.defn(name="DocumentProcessingWorkflow")
class DocumentProcessingWorkflow:
    """
    Workflow for processing a single document.

    Steps:
    1. Download document from MinIO
    2. Convert PDF to images
    3. Analyze with LangChain + Claude vision
    4. Save results to database
    5. Update status
    """

    @workflow.run
    async def run(self, document_id: int, minio_key: str, document_type: str) -> Dict[str, Any]:
        """
        Run the document processing workflow.

        Args:
            document_id: Database ID of the document
            minio_key: MinIO object key
            document_type: Type of document (pv_ag, diagnostic, etc.)

        Returns:
            Dict with processing results
        """
        workflow.logger.info(f"Starting document processing workflow for document {document_id}")

        # Define retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        try:
            # Step 1: Update status to processing
            await workflow.execute_activity(
                update_document_status,
                args=[document_id, "processing", None],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            # Step 2: Download from MinIO
            file_data = await workflow.execute_activity(
                download_from_minio,
                args=[minio_key],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            # Step 3: Calculate file hash (for deduplication tracking)
            file_hash = await workflow.execute_activity(
                calculate_file_hash,
                args=[file_data],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            # Step 4: Convert PDF to images
            images_base64 = await workflow.execute_activity(
                pdf_to_images,
                args=[file_data],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

            # Step 5: Analyze with LangChain
            analysis_result = await workflow.execute_activity(
                analyze_with_langchain,
                args=[images_base64, document_id, document_type],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

            # Step 6: Save results
            await workflow.execute_activity(
                save_analysis_results,
                args=[document_id, analysis_result],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )

            # Step 7: Update status to completed
            await workflow.execute_activity(
                update_document_status,
                args=[document_id, "completed", None],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            workflow.logger.info(f"Document processing workflow completed for document {document_id}")

            return {
                "document_id": document_id,
                "status": "completed",
                "file_hash": file_hash,
                "pages_processed": len(images_base64),
                "tokens_used": analysis_result.get("tokens_used", 0),
                "estimated_cost": analysis_result.get("estimated_cost", 0.0),
            }

        except Exception as e:
            workflow.logger.error(f"Document processing workflow failed for document {document_id}: {e}")

            # Update status to failed
            await workflow.execute_activity(
                update_document_status,
                args=[document_id, "failed", str(e)],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(e),
            }


@workflow.defn(name="DocumentAggregationWorkflow")
class DocumentAggregationWorkflow:
    """
    Workflow for aggregating multiple documents of the same category.

    This workflow is triggered after multiple documents are processed
    to create a combined summary (e.g., all PV d'AG for a property).
    """

    @workflow.run
    async def run(self, property_id: int, category: str, document_ids: list[int]) -> Dict[str, Any]:
        """
        Run the document aggregation workflow.

        Args:
            property_id: Database ID of the property
            category: Document category (pv_ag, diagnostic, etc.)
            document_ids: List of document IDs to aggregate

        Returns:
            Dict with aggregation results
        """
        workflow.logger.info(
            f"Starting document aggregation workflow for property {property_id}, "
            f"category {category}, {len(document_ids)} documents"
        )

        # TODO: Implement aggregation workflow
        # This would:
        # 1. Fetch all document summaries from database
        # 2. Use LangChain to create aggregated summary
        # 3. Save to DocumentSummary table

        # For now, return placeholder
        return {
            "property_id": property_id,
            "category": category,
            "num_documents": len(document_ids),
            "status": "completed",
        }


@workflow.defn(name="BulkDocumentProcessingWorkflow")
class BulkDocumentProcessingWorkflow:
    """
    Workflow for processing multiple documents in bulk using LangGraph.

    This workflow:
    1. Accepts multiple document uploads
    2. Uses LangGraph agent to classify and route documents
    3. Processes documents in parallel using child workflows
    4. Synthesizes results across all documents
    5. Saves aggregated summary to database
    """

    @workflow.run
    async def run(self, property_id: int, document_uploads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the bulk document processing workflow.

        Args:
            property_id: Database ID of the property
            document_uploads: List of dicts with {
                "document_id": int,
                "minio_key": str,
                "filename": str
            }

        Returns:
            Dict with bulk processing results including synthesis
        """
        workflow.logger.info(
            f"Starting bulk document processing for property {property_id}, "
            f"{len(document_uploads)} documents"
        )

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        try:
            # Step 1: Download all files from MinIO in parallel
            download_tasks = []
            for upload in document_uploads:
                task = workflow.execute_activity(
                    download_from_minio,
                    args=[upload["minio_key"]],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                download_tasks.append(task)

            # Wait for all downloads
            file_data_list = await asyncio.gather(*download_tasks)

            # Step 2: Convert all PDFs to images in parallel
            conversion_tasks = []
            for file_data in file_data_list:
                task = workflow.execute_activity(
                    pdf_to_images,
                    args=[file_data],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=retry_policy,
                )
                conversion_tasks.append(task)

            # Wait for all conversions
            all_images_list = await asyncio.gather(*conversion_tasks)

            # Step 3: Use LangGraph agent to classify, route, and process
            # Prepare documents for the agent
            agent_documents = []
            for i, upload in enumerate(document_uploads):
                agent_documents.append({
                    "filename": upload["filename"],
                    "file_data_base64": all_images_list[i],
                    "document_id": upload["document_id"]
                })

            # Execute LangGraph workflow
            agent_result = await workflow.execute_activity(
                run_langgraph_agent,
                args=[agent_documents, property_id],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=retry_policy,
            )

            # Step 4: Save individual document results in parallel
            save_tasks = []
            for result in agent_result["processing_results"]:
                if "error" not in result:
                    # Find matching document_id
                    doc_id = next(
                        (d["document_id"] for d in document_uploads if d["filename"] == result["filename"]),
                        None
                    )
                    if doc_id:
                        task = workflow.execute_activity(
                            save_analysis_results,
                            args=[doc_id, result["result"]],
                            start_to_close_timeout=timedelta(seconds=60),
                            retry_policy=retry_policy,
                        )
                        save_tasks.append(task)

            await asyncio.gather(*save_tasks)

            # Step 5: Update all document statuses in parallel
            status_tasks = []
            for upload in document_uploads:
                task = workflow.execute_activity(
                    update_document_status,
                    args=[upload["document_id"], "completed", None],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )
                status_tasks.append(task)

            await asyncio.gather(*status_tasks)

            # Step 6: Save synthesis to DocumentSummary table
            await workflow.execute_activity(
                save_document_synthesis,
                args=[property_id, agent_result["synthesis"]],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=retry_policy,
            )

            workflow.logger.info(f"Bulk processing complete for property {property_id}")

            return {
                "property_id": property_id,
                "status": "completed",
                "documents_processed": len(document_uploads),
                "synthesis": agent_result["synthesis"],
                "total_tokens": agent_result.get("total_tokens", 0),
                "total_cost": agent_result.get("total_cost", 0.0)
            }

        except Exception as e:
            workflow.logger.error(f"Bulk processing failed for property {property_id}: {e}")

            # Update all documents to failed status
            for upload in document_uploads:
                await workflow.execute_activity(
                    update_document_status,
                    args=[upload["document_id"], "failed", str(e)],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

            return {
                "property_id": property_id,
                "status": "failed",
                "error": str(e)
            }
