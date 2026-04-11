"""PDF report export endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.better_auth_security import get_current_user_hybrid as get_current_user
from app.core.database import get_db
from app.core.i18n import get_local
from app.models.property import Property
from app.services.pdf_service import (
    generate_full_report_pdf,
    generate_price_analysis_pdf,
    generate_synthesis_pdf,
    sanitize_filename,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_owned_property(property_id: int, current_user: str, db: Session) -> Property:
    """Fetch a property that belongs to the current user, or raise 404."""
    property_obj = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return property_obj


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    """Build a FastAPI Response for a PDF download."""
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{property_id}/report/pdf")
async def download_full_report(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Download a comprehensive PDF report for a property."""
    locale = get_local(request)
    property_obj = _get_owned_property(property_id, current_user, db)

    try:
        pdf_bytes = generate_full_report_pdf(property_obj, db, locale)
    except Exception:
        logger.exception(f"Failed to generate full report PDF for property {property_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report",
        )

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    address_clean = sanitize_filename(property_obj.address or "property")
    filename = f"AppArt_Agent_Report_{address_clean}_{date_str}.pdf"
    return _pdf_response(pdf_bytes, filename)


@router.get("/{property_id}/report/price-analysis/pdf")
async def download_price_analysis_pdf(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Download a PDF of the price analysis section only."""
    locale = get_local(request)
    property_obj = _get_owned_property(property_id, current_user, db)

    try:
        pdf_bytes = generate_price_analysis_pdf(property_obj, db, locale)
    except Exception:
        logger.exception(f"Failed to generate price analysis PDF for property {property_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report",
        )

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    address_clean = sanitize_filename(property_obj.address or "property")
    filename = f"AppArt_Agent_Price_Analysis_{address_clean}_{date_str}.pdf"
    return _pdf_response(pdf_bytes, filename)


@router.get("/{property_id}/report/synthesis/pdf")
async def download_synthesis_pdf(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Download a PDF of the document synthesis section only."""
    locale = get_local(request)
    property_obj = _get_owned_property(property_id, current_user, db)

    try:
        pdf_bytes = generate_synthesis_pdf(property_obj, db, locale)
    except Exception:
        logger.exception(f"Failed to generate synthesis PDF for property {property_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report",
        )

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    address_clean = sanitize_filename(property_obj.address or "property")
    filename = f"AppArt_Agent_Synthesis_{address_clean}_{date_str}.pdf"
    return _pdf_response(pdf_bytes, filename)
