"""
Webhook endpoints for external services.

Handles MinIO bucket notifications and other external service callbacks.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/minio")
async def minio_webhook(request: Request) -> Dict[str, str]:
    """
    Handle MinIO bucket notifications.

    Currently logs the webhook event. Document processing is handled
    via the bulk-upload endpoint with async processing.
    """
    try:
        payload = await request.json()
        logger.info(f"MinIO webhook: {payload.get('EventName')}")

        records = payload.get("Records", [])
        if not records:
            return {"status": "ignored", "reason": "no_records"}

        for record in records:
            event_name = record.get("eventName", "")
            object_key = record.get("s3", {}).get("object", {}).get("key", "")
            logger.info(f"MinIO event: {event_name} - {object_key}")

        return {"status": "success", "message": "Webhook received"}

    except Exception as e:
        logger.error(f"MinIO webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health() -> Dict[str, str]:
    """Health check endpoint for webhooks."""
    return {"status": "healthy"}
