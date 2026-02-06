"""Pydantic schemas for request/response validation."""

from app.schemas.document import (
    DiagnosticAnalysisResponse,
    DocumentResponse,
    DocumentUpload,
    PVAGAnalysisResponse,
    TaxChargesAnalysisResponse,
)
from app.schemas.property import (
    DVFRecordResponse,
    PriceAnalysisResponse,
    PropertyBase,
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
)

__all__ = [
    "PropertyBase",
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "DVFRecordResponse",
    "PriceAnalysisResponse",
    "DocumentUpload",
    "DocumentResponse",
    "PVAGAnalysisResponse",
    "DiagnosticAnalysisResponse",
    "TaxChargesAnalysisResponse",
]
