"""Property schemas for request/response validation."""

from datetime import date, datetime
from typing import List, Optional, Union

from pydantic import BaseModel, field_validator


class PropertyBase(BaseModel):
    """Base property schema."""

    address: str
    postal_code: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None
    asking_price: Optional[float] = None
    surface_area: Optional[float] = None
    rooms: Optional[int] = None
    property_type: Optional[str] = None
    floor: Optional[int] = None
    building_floors: Optional[int] = None
    building_year: Optional[int] = None


class PropertyCreate(PropertyBase):
    """Schema for creating a new property."""

    pass


class PropertyUpdate(BaseModel):
    """Schema for updating a property."""

    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None
    asking_price: Optional[float] = None
    surface_area: Optional[float] = None
    rooms: Optional[int] = None
    property_type: Optional[str] = None
    floor: Optional[int] = None
    building_floors: Optional[int] = None
    building_year: Optional[int] = None


class PropertyResponse(PropertyBase):
    """Schema for property response."""

    id: int
    user_id: int
    estimated_value: Optional[float] = None
    price_per_sqm: Optional[float] = None
    market_comparison_score: Optional[float] = None
    recommendation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DVFSaleLotResponse(BaseModel):
    """Schema for individual lot in a DVF sale."""

    id: int
    lot_type: Optional[str] = None
    nature_culture: Optional[str] = None
    surface_bati: Optional[int] = None
    nombre_pieces: Optional[int] = None
    surface_terrain: Optional[int] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    class Config:
        from_attributes = True


class DVFSaleResponse(BaseModel):
    """
    Schema for DVF sale response.

    Maps new DVFSale columns to the old API field names for backward compatibility.
    Frontend receives the same JSON shape as before.
    """

    id: int
    sale_date: Union[datetime, date]
    sale_price: float
    address: str
    postal_code: str
    city: str
    property_type: str
    surface_area: Optional[int] = None
    rooms: Optional[int] = None
    price_per_sqm: Optional[float] = None
    unit_count: Optional[int] = 1
    is_multi_unit: Optional[bool] = False
    is_outlier: Optional[bool] = False
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    @field_validator("sale_date", mode="before")
    @classmethod
    def convert_date_to_datetime(cls, v):
        """Convert date to datetime for consistent API response."""
        if isinstance(v, date) and not isinstance(v, datetime):
            return datetime.combine(v, datetime.min.time())
        return v

    class Config:
        from_attributes = True

    @classmethod
    def from_dvf_sale(cls, sale, is_outlier: bool = False) -> "DVFSaleResponse":
        """Create response from a DVFSale model instance."""
        return cls(
            id=sale.id,
            sale_date=sale.date_mutation,
            sale_price=float(sale.prix) if sale.prix else 0,
            address=sale.adresse_complete or "",
            postal_code=sale.code_postal or "",
            city=sale.nom_commune or "",
            property_type=sale.type_principal or "",
            surface_area=sale.surface_bati,
            rooms=sale.nombre_pieces,
            price_per_sqm=float(sale.prix_m2) if sale.prix_m2 else None,
            unit_count=sale.nombre_lots,
            is_multi_unit=(sale.nombre_lots or 1) > 1,
            is_outlier=is_outlier,
            longitude=sale.longitude,
            latitude=sale.latitude,
        )


class PropertySynthesisPreview(BaseModel):
    """Preview of property document synthesis for dashboard cards."""

    risk_level: Optional[str] = None
    total_annual_cost: Optional[float] = None
    total_one_time_cost: Optional[float] = None
    key_findings: Optional[List[str]] = None
    document_count: int = 0
    redesign_count: int = 0


class PropertyWithSynthesisResponse(PropertyResponse):
    """Property response enriched with synthesis preview data."""

    synthesis: Optional[PropertySynthesisPreview] = None

    class Config:
        from_attributes = True


class PriceAnalysisResponse(BaseModel):
    """Schema for price analysis response (legacy)."""

    estimated_value: float
    price_per_sqm: float
    market_avg_price_per_sqm: float
    market_median_price_per_sqm: Optional[float] = None
    price_deviation_percent: float
    comparable_sales: list[DVFSaleResponse]
    recommendation: str
    confidence_score: float
    comparables_count: Optional[int] = None
    market_trend_annual: Optional[float] = None
    analysis_type: Optional[str] = None
    trend_projection: Optional[dict] = None


class PriceAnalysisSummaryResponse(BaseModel):
    """Compact summary for the property detail summary card."""

    estimated_value: Optional[float] = None
    price_deviation_percent: Optional[float] = None
    recommendation: Optional[str] = None
    confidence_score: Optional[float] = None
    comparables_count: Optional[int] = None
    estimated_value_2025: Optional[float] = None
    trend_used: Optional[float] = None
    updated_at: Optional[datetime] = None
    is_stale: bool = False

    class Config:
        from_attributes = True


class ExcludeSalesRequest(BaseModel):
    """Request body for persisting sale exclusions."""

    excluded_sale_ids: List[int] = []
    excluded_neighboring_sale_ids: List[int] = []


class PriceAnalysisFullResponse(PriceAnalysisSummaryResponse):
    """Full data for the Price Analyst page."""

    price_per_sqm: Optional[float] = None
    market_avg_price_per_sqm: Optional[float] = None
    market_median_price_per_sqm: Optional[float] = None
    market_trend_annual: Optional[float] = None
    projected_price_per_sqm: Optional[float] = None
    trend_source: Optional[str] = None
    trend_sample_size: Optional[int] = None
    comparable_sales: Optional[list] = None
    trend_projection: Optional[dict] = None
    market_trend: Optional[dict] = None
    excluded_sale_ids: List[int] = []
    excluded_neighboring_sale_ids: List[int] = []

    class Config:
        from_attributes = True
