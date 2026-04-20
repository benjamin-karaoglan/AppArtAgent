"""Properties API routes."""

import json
import logging
import statistics
from collections import defaultdict
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.better_auth_security import get_current_user_hybrid as get_current_user
from app.core.cache import cache_get, cache_set, get_redis
from app.core.database import get_db
from app.core.i18n import get_local, translate
from app.models.document import Document, DocumentSummary
from app.models.photo import Photo, PhotoRedesign
from app.models.price_analysis import PriceAnalysis
from app.models.property import DVFSale, Property
from app.schemas.property import (
    ExcludeSalesRequest,
    PriceAnalysisFullResponse,
    PriceAnalysisSummaryResponse,
    PropertyCreate,
    PropertyResponse,
    PropertySynthesisPreview,
    PropertyUpdate,
    PropertyWithSynthesisResponse,
)
from app.services.dvf_service import DVFService, _street_ilike_pattern, dvf_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AddressSearchResult(BaseModel):
    """Address search result — one per street + postal code."""

    address: str  # Street name (e.g. "RUE NOTRE-DAME DES CHAMPS")
    postal_code: str
    city: str
    property_type: str
    count: int  # Number of sales on this street


class DVFStatsResponse(BaseModel):
    """DVF statistics response."""

    total_records: int
    total_imports: int
    last_updated: str | None
    formatted_count: str  # Human-readable format like "1.36M"


@router.get("/dvf-stats", response_model=DVFStatsResponse)
async def get_dvf_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get DVF database statistics.
    Returns total records count and last update time.
    Public endpoint - no authentication required for dashboard stats.
    """
    get_local(request)

    # Check Redis cache first
    cached = cache_get("dvf_stats")
    if cached:
        return DVFStatsResponse(**json.loads(cached))

    total = db.query(func.count(DVFSale.id)).scalar() or 0

    # Format the count for display
    if total >= 1_000_000:
        formatted = f"{total / 1_000_000:.2f}M"
    elif total >= 1_000:
        formatted = f"{total / 1_000:.1f}K"
    else:
        formatted = str(total)

    result = DVFStatsResponse(
        total_records=total,
        total_imports=0,
        last_updated=None,
        formatted_count=formatted,
    )

    # Cache for 1 hour — count only changes on DVF import
    cache_set("dvf_stats", json.dumps(result.model_dump()), 3600)

    return result


@router.get("/search-addresses", response_model=List[AddressSearchResult])
async def search_addresses(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query (at least 2 characters)"),
    postal_code: str = Query(None, description="Filter by postal code"),
    limit: int = Query(20, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Search for streets in DVF database.

    Strips leading number from query so "35 rue notre dame" finds
    all sales on "RUE NOTRE-DAME DES CHAMPS" regardless of house number.
    Results are grouped by street + postal code + city.
    """
    get_local(request)

    # Strip leading number: "35 rue notre dame" → "rue notre dame"
    _, street_name = DVFService.extract_street_info(q)
    search_text = street_name if street_name else q

    # Normalize for fuzzy matching: "notre dame" → "NOTRE%DAME"
    search_pattern = _street_ilike_pattern(search_text)

    # Group by street name (adresse_nom_voie), not full address
    query = db.query(
        DVFSale.adresse_nom_voie,
        DVFSale.code_postal,
        DVFSale.nom_commune,
        func.string_agg(func.distinct(DVFSale.type_principal), ", ").label("property_types"),
        func.count(DVFSale.id).label("count"),
    ).filter(
        DVFSale.adresse_nom_voie.isnot(None),
        DVFSale.adresse_nom_voie != "",
        DVFSale.adresse_nom_voie.ilike(f"%{search_pattern}%"),
    )

    if postal_code:
        query = query.filter(DVFSale.code_postal == postal_code)

    query = (
        query.group_by(DVFSale.adresse_nom_voie, DVFSale.code_postal, DVFSale.nom_commune)
        .order_by(func.count(DVFSale.id).desc())
        .limit(limit)
    )

    results = query.all()

    return [
        AddressSearchResult(
            address=r.adresse_nom_voie,
            postal_code=r.code_postal,
            city=r.nom_commune,
            property_type=r.property_types or "Appartement",
            count=r.count,
        )
        for r in results
    ]


@router.get("/with-synthesis", response_model=List[PropertyWithSynthesisResponse])
async def list_properties_with_synthesis(
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all properties for the current user with synthesis preview data."""
    get_local(request)

    properties = (
        db.query(Property)
        .filter(Property.user_id == int(current_user))
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not properties:
        return []

    prop_ids = [p.id for p in properties]

    # Batch fetch syntheses (one query instead of N)
    syntheses = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.property_id.in_(prop_ids),
            DocumentSummary.category == None,
        )
        .all()
    )
    synthesis_map = {s.property_id: s for s in syntheses}

    # Batch fetch document counts (one query instead of N)
    doc_counts = (
        db.query(Document.property_id, func.count(Document.id))
        .filter(Document.property_id.in_(prop_ids))
        .group_by(Document.property_id)
        .all()
    )
    doc_count_map: dict[int, int] = dict(doc_counts)

    # Batch fetch redesign counts (one query instead of N)
    redesign_counts = (
        db.query(Photo.property_id, func.count(PhotoRedesign.id))
        .join(PhotoRedesign, PhotoRedesign.photo_id == Photo.id)
        .filter(Photo.property_id.in_(prop_ids))
        .group_by(Photo.property_id)
        .all()
    )
    redesign_count_map: dict[int, int] = dict(redesign_counts)

    result = []
    for prop in properties:
        synthesis = synthesis_map.get(prop.id)
        doc_count = doc_count_map.get(prop.id, 0)
        redesign_count = redesign_count_map.get(prop.id, 0)

        synthesis_preview = None
        if synthesis:
            key_findings: list[str] = synthesis.key_findings or []
            synthesis_preview = PropertySynthesisPreview(
                risk_level=synthesis.risk_level,
                total_annual_cost=synthesis.total_annual_cost,
                total_one_time_cost=synthesis.total_one_time_cost,
                key_findings=key_findings,
                document_count=doc_count,
                redesign_count=redesign_count,
            )
        elif doc_count > 0 or redesign_count > 0:
            synthesis_preview = PropertySynthesisPreview(
                document_count=doc_count,
                redesign_count=redesign_count,
            )

        prop_response = PropertyWithSynthesisResponse.model_validate(prop)
        prop_response.synthesis = synthesis_preview
        result.append(prop_response)

    return result


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    request: Request,
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Create a new property for analysis."""
    get_local(request)

    property = Property(**property_data.dict(), user_id=int(current_user))

    if property.asking_price and property.surface_area:
        property.price_per_sqm = property.asking_price / property.surface_area

    db.add(property)
    db.commit()
    db.refresh(property)
    return property


@router.get("/", response_model=List[PropertyResponse])
async def list_properties(
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all properties for the current user."""
    get_local(request)

    properties = (
        db.query(Property)
        .filter(Property.user_id == int(current_user))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return properties


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Get a specific property by ID."""
    locale = get_local(request)

    property = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )

    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    return property


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    request: Request,
    property_update: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Update a property."""
    locale = get_local(request)

    property = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )

    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    for field, value in property_update.dict(exclude_unset=True).items():
        setattr(property, field, value)

    if property.asking_price and property.surface_area:
        property.price_per_sqm = property.asking_price / property.surface_area

    db.commit()
    db.refresh(property)
    return property


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Delete a property."""
    locale = get_local(request)

    property = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )

    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    db.delete(property)
    db.commit()
    return None


def _serialize_sale(sale: DVFSale, is_outlier: bool = False) -> dict:
    """Serialize a DVFSale to a JSON-safe dict for persistence."""
    result = {
        "id": sale.id,
        "address": sale.adresse_complete or "",
        "sale_date": sale.date_mutation.isoformat()
        if hasattr(sale.date_mutation, "isoformat")
        else str(sale.date_mutation),
        "sale_price": float(sale.prix) if sale.prix else 0,
        "postal_code": sale.code_postal or "",
        "city": sale.nom_commune or "",
        "property_type": sale.type_principal or "",
        "surface_area": sale.surface_bati,
        "rooms": sale.nombre_pieces,
        "price_per_sqm": float(sale.prix_m2) if sale.prix_m2 else None,
        "unit_count": sale.nombre_lots,
        "is_multi_unit": (sale.nombre_lots or 1) > 1,
        "is_outlier": is_outlier,
        "longitude": sale.longitude,
        "latitude": sale.latitude,
    }

    # Include individual lot details for multi-unit sales
    if (sale.nombre_lots or 1) > 1 and hasattr(sale, "lots") and sale.lots:
        total_surface = sum(lot.surface_bati or 0 for lot in sale.lots)
        result["lots_detail"] = [
            {
                "lot_type": lot.lot_type,
                "surface_area": lot.surface_bati,
                "rooms": lot.nombre_pieces,
                "price_per_sqm": (
                    round(float(sale.prix) / total_surface, 2)
                    if sale.prix and total_surface > 0 and lot.surface_bati
                    else None
                ),
            }
            for lot in sale.lots
        ]
        # Use actual lot count from data (nombre_lots can be unreliable)
        result["unit_count"] = len(sale.lots)

    return result


def _compute_market_trend_json(property_obj: Property, db: Session) -> dict:
    """Compute yearly market trend data for chart."""
    neighboring_sales = dvf_service.get_neighboring_sales_for_trend(
        db=db,
        postal_code=property_obj.postal_code or "",
        property_type=property_obj.property_type or "Appartement",
    )

    if not neighboring_sales:
        return {
            "years": [],
            "average_prices": [],
            "year_over_year_changes": [],
            "sample_counts": [],
            "total_sales": 0,
            "outliers_excluded": 0,
        }

    outlier_flags = dvf_service.detect_outliers_iqr(neighboring_sales)
    filtered_sales = [sale for i, sale in enumerate(neighboring_sales) if not outlier_flags[i]]
    outliers_excluded = len(neighboring_sales) - len(filtered_sales)

    sales_by_year: dict[int, list[float]] = defaultdict(list)
    for sale in filtered_sales:
        if sale.date_mutation and sale.prix_m2 and float(sale.prix_m2) > 0:
            sales_by_year[sale.date_mutation.year].append(float(sale.prix_m2))

    sorted_years = sorted(sales_by_year.keys())
    years = []
    average_prices = []
    year_over_year_changes = []
    sample_counts = []

    for i, year in enumerate(sorted_years):
        median_price = statistics.median(sales_by_year[year])
        years.append(year)
        average_prices.append(round(median_price, 2))
        sample_counts.append(len(sales_by_year[year]))
        if i > 0:
            prev_median = statistics.median(sales_by_year[sorted_years[i - 1]])
            yoy_change = ((median_price - prev_median) / prev_median) * 100
            year_over_year_changes.append(round(yoy_change, 2))
        else:
            year_over_year_changes.append(0)

    return {
        "years": years,
        "average_prices": average_prices,
        "year_over_year_changes": year_over_year_changes,
        "sample_counts": sample_counts,
        "postal_code": property_obj.postal_code or "",
        "total_sales": len(neighboring_sales),
        "outliers_excluded": outliers_excluded,
    }


def _run_trend_analysis(
    property_obj: Property,
    db: Session,
    locale: str = "fr",
    excluded_sale_ids: list[int] | None = None,
    excluded_neighboring_sale_ids: list[int] | None = None,
) -> PriceAnalysis:
    """
    Run full trend analysis, persist results, return PriceAnalysis row.

    excluded_sale_ids / excluded_neighboring_sale_ids are the **complete**
    exclusion lists (including auto-detected outliers on first run).
    The backend uses ONLY these lists to decide what is excluded — there is
    no additional auto-outlier filtering on top.
    """
    excluded_sale_ids = excluded_sale_ids or []
    excluded_neighboring_sale_ids = excluded_neighboring_sale_ids or []

    exact_sales = dvf_service.get_exact_address_sales(
        db=db,
        postal_code=property_obj.postal_code or "",
        property_type=property_obj.property_type or "Appartement",
        address=property_obj.address or "",
    )

    neighboring_sales = dvf_service.get_neighboring_sales_for_trend(
        db=db,
        postal_code=property_obj.postal_code or "",
        property_type=property_obj.property_type or "Appartement",
    )

    # Detect outliers
    neighboring_outlier_flags = dvf_service.detect_outliers_iqr(neighboring_sales)

    # On first run (empty exclusion lists), auto-populate with detected outlier IDs
    if not excluded_neighboring_sale_ids:
        excluded_neighboring_sale_ids = [
            int(sale.id) for i, sale in enumerate(neighboring_sales) if neighboring_outlier_flags[i]
        ]

    # Filter neighboring sales using the persisted exclusion list only
    excluded_neighboring_set = set(excluded_neighboring_sale_ids)
    filtered_neighboring_sales = [
        sale for sale in neighboring_sales if sale.id not in excluded_neighboring_set
    ]

    # Trend projection
    trend_projection = dvf_service.calculate_trend_based_projection(
        exact_address_sales=exact_sales,
        neighboring_sales=filtered_neighboring_sales,
        surface_area=property_obj.surface_area,
    )

    # Price analysis on comparable sales
    comparable_for_analysis = exact_sales if exact_sales else neighboring_sales

    # Eagerly load lot details for multi-unit sales (needed for serialization)
    multi_unit_ids = [sale.id for sale in comparable_for_analysis if (sale.nombre_lots or 1) > 1]
    if multi_unit_ids:
        from app.models.property import DVFSaleLot

        lots_by_mutation = defaultdict(list)
        lots = (
            db.query(DVFSaleLot)
            .join(DVFSale, DVFSaleLot.id_mutation == DVFSale.id_mutation)
            .filter(DVFSale.id.in_(multi_unit_ids))
            .all()
        )
        for lot in lots:
            lots_by_mutation[lot.id_mutation].append(lot)
        for sale in comparable_for_analysis:
            if sale.id in multi_unit_ids:
                sale.lots = lots_by_mutation.get(sale.id_mutation, [])

    outlier_flags = dvf_service.detect_outliers_iqr(comparable_for_analysis)

    # On first run, auto-populate with detected outlier IDs
    if not excluded_sale_ids:
        excluded_sale_ids = [
            int(sale.id) for i, sale in enumerate(comparable_for_analysis) if outlier_flags[i]
        ]

    # Build exclude indices from the persisted exclusion list only
    excluded_sale_set = set(excluded_sale_ids)
    exclude_indices = [
        i for i, sale in enumerate(comparable_for_analysis) if sale.id in excluded_sale_set
    ]

    analysis = dvf_service.calculate_price_analysis(
        asking_price=property_obj.asking_price,
        surface_area=property_obj.surface_area,
        comparable_sales=comparable_for_analysis,
        exclude_indices=exclude_indices,
        apply_time_adjustment=False,
        locale=locale,
    )

    # Build serialized comparable sales (with lots detail for multi-unit sales)
    comparable_sales_json = [
        _serialize_sale(sale, is_outlier=outlier_flags[i] if i < len(outlier_flags) else False)
        for i, sale in enumerate(comparable_for_analysis)
    ]

    # Build trend projection with neighboring sales (ensure date objects are serialized)
    trend_projection_json = {
        k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in trend_projection.items()
    }
    trend_projection_json["neighboring_sales"] = [
        {
            **_serialize_sale(
                sale,
                is_outlier=neighboring_outlier_flags[i]
                if i < len(neighboring_outlier_flags)
                else False,
            ),
        }
        for i, sale in enumerate(neighboring_sales)
    ]

    # Compute market trend for chart
    market_trend_json = _compute_market_trend_json(property_obj, db)

    # Upsert PriceAnalysis
    pa = db.query(PriceAnalysis).filter(PriceAnalysis.property_id == property_obj.id).first()
    if not pa:
        pa = PriceAnalysis(property_id=property_obj.id)
        db.add(pa)

    pa.estimated_value = analysis["estimated_value"]
    pa.price_per_sqm = analysis["price_per_sqm"]
    pa.market_avg_price_per_sqm = analysis["market_avg_price_per_sqm"]
    pa.market_median_price_per_sqm = analysis.get("market_median_price_per_sqm")
    pa.price_deviation_percent = analysis["price_deviation_percent"]
    pa.confidence_score = analysis["confidence_score"]
    pa.market_trend_annual = analysis.get("market_trend_annual")
    pa.recommendation = analysis["recommendation"]
    pa.comparables_count = analysis.get("comparables_count")

    pa.estimated_value_2025 = trend_projection.get("estimated_value_2025")
    pa.projected_price_per_sqm = trend_projection.get("projected_price_per_sqm")
    pa.trend_used = trend_projection.get("trend_used")
    pa.trend_source = trend_projection.get("trend_source")
    pa.trend_sample_size = trend_projection.get("trend_sample_size")

    pa.comparable_sales_json = comparable_sales_json
    pa.trend_projection_json = trend_projection_json
    pa.market_trend_json = market_trend_json

    pa.excluded_sale_ids = excluded_sale_ids
    pa.excluded_neighboring_sale_ids = excluded_neighboring_sale_ids

    # Also update property-level fields
    property_obj.estimated_value = analysis["estimated_value"]
    property_obj.market_comparison_score = analysis["confidence_score"]
    property_obj.recommendation = analysis["recommendation"]

    # Set pa.updated_at AFTER property updates so it's always >= property.updated_at
    # (property.updated_at has onupdate=datetime.utcnow which fires on commit)
    now = datetime.utcnow()
    pa.updated_at = now
    property_obj.updated_at = now

    db.commit()
    db.refresh(pa)
    return pa


def _is_stale(pa: PriceAnalysis, property_obj: Property) -> bool:
    """Check if analysis is stale (property updated after analysis, or >30 days old)."""
    if not pa.updated_at:
        return True
    if property_obj.updated_at and property_obj.updated_at > pa.updated_at:
        return True
    if (datetime.utcnow() - pa.updated_at).days > 30:
        return True
    return False


def _pa_to_summary(pa: PriceAnalysis, stale: bool) -> dict:
    """Convert PriceAnalysis row to summary dict."""
    return {
        "estimated_value": pa.estimated_value,
        "price_deviation_percent": pa.price_deviation_percent,
        "recommendation": pa.recommendation,
        "confidence_score": pa.confidence_score,
        "comparables_count": pa.comparables_count,
        "estimated_value_2025": pa.estimated_value_2025,
        "trend_used": pa.trend_used,
        "updated_at": pa.updated_at,
        "is_stale": stale,
    }


def _pa_to_full(pa: PriceAnalysis, stale: bool) -> dict:
    """Convert PriceAnalysis row to full dict."""
    return {
        **_pa_to_summary(pa, stale),
        "price_per_sqm": pa.price_per_sqm,
        "market_avg_price_per_sqm": pa.market_avg_price_per_sqm,
        "market_median_price_per_sqm": pa.market_median_price_per_sqm,
        "market_trend_annual": pa.market_trend_annual,
        "projected_price_per_sqm": pa.projected_price_per_sqm,
        "trend_source": pa.trend_source,
        "trend_sample_size": pa.trend_sample_size,
        "comparable_sales": pa.comparable_sales_json or [],
        "trend_projection": pa.trend_projection_json,
        "market_trend": pa.market_trend_json,
        "excluded_sale_ids": pa.excluded_sale_ids or [],
        "excluded_neighboring_sale_ids": pa.excluded_neighboring_sale_ids or [],
    }


def _get_or_run_analysis(
    property_obj: Property, db: Session, locale: str, auto_refresh_if_stale: bool = False
) -> tuple[PriceAnalysis | None, bool]:
    """
    Get cached analysis or auto-run if missing.
    Returns (PriceAnalysis, is_stale) or (None, False) if can't run.
    """
    pa = db.query(PriceAnalysis).filter(PriceAnalysis.property_id == property_obj.id).first()

    if pa:
        stale = _is_stale(pa, property_obj)
        if stale and auto_refresh_if_stale:
            pa = _run_trend_analysis(
                property_obj,
                db,
                locale,
                excluded_sale_ids=pa.excluded_sale_ids or [],
                excluded_neighboring_sale_ids=pa.excluded_neighboring_sale_ids or [],
            )
            return pa, False
        return pa, stale

    # No existing analysis — auto-run if property has required fields
    if property_obj.asking_price and property_obj.surface_area:
        pa = _run_trend_analysis(property_obj, db, locale)
        return pa, False

    return None, False


@router.get("/{property_id}/price-analysis", response_model=PriceAnalysisSummaryResponse)
async def get_price_analysis_summary(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get price analysis summary. Auto-runs on first visit if property has
    asking_price + surface_area. Returns cached results on subsequent visits.
    """
    locale = get_local(request)

    # Check Redis cache first
    cache_key = f"price_analysis_summary:{property_id}"
    cached = cache_get(cache_key)
    if cached:
        return PriceAnalysisSummaryResponse(**json.loads(cached))

    property_obj = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    pa, _stale = _get_or_run_analysis(property_obj, db, locale, auto_refresh_if_stale=True)
    if not pa:
        return PriceAnalysisSummaryResponse()

    result = _pa_to_summary(pa, False)

    # Cache for 30 min
    cache_set(cache_key, json.dumps(result, default=str), 1800)

    return PriceAnalysisSummaryResponse(**result)


@router.get("/{property_id}/price-analysis/full", response_model=PriceAnalysisFullResponse)
async def get_price_analysis_full(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Get full price analysis data for the Price Analyst page."""
    locale = get_local(request)

    # Check Redis cache first
    cache_key = f"price_analysis_full:{property_id}"
    cached = cache_get(cache_key)
    if cached:
        return PriceAnalysisFullResponse(**json.loads(cached))

    property_obj = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    pa, _stale = _get_or_run_analysis(property_obj, db, locale, auto_refresh_if_stale=True)
    if not pa:
        return PriceAnalysisFullResponse()

    result = _pa_to_full(pa, False)

    # Cache for 30 min
    cache_set(cache_key, json.dumps(result, default=str), 1800)

    return PriceAnalysisFullResponse(**result)


@router.post("/{property_id}/price-analysis/refresh", response_model=PriceAnalysisFullResponse)
async def refresh_price_analysis(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Force re-run analysis with fresh DVF data."""
    locale = get_local(request)

    property_obj = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    if not property_obj.asking_price or not property_obj.surface_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translate("property_needs_price_surface", locale),
        )

    # Preserve user exclusions from existing analysis
    existing = db.query(PriceAnalysis).filter(PriceAnalysis.property_id == property_obj.id).first()
    excluded_sale_ids: list[int] = existing.excluded_sale_ids if existing else []
    excluded_neighboring: list[int] = existing.excluded_neighboring_sale_ids if existing else []

    pa = _run_trend_analysis(
        property_obj,
        db,
        locale,
        excluded_sale_ids=excluded_sale_ids or [],
        excluded_neighboring_sale_ids=excluded_neighboring or [],
    )

    # Invalidate cached price analysis
    try:
        r = get_redis()
        r.delete(f"price_analysis_summary:{property_id}", f"price_analysis_full:{property_id}")
    except Exception:
        logger.debug("Failed to invalidate price analysis cache for property %s", property_id)

    return PriceAnalysisFullResponse(**_pa_to_full(pa, False))


@router.post(
    "/{property_id}/price-analysis/exclude-sales", response_model=PriceAnalysisFullResponse
)
async def exclude_sales(
    property_id: int,
    request: Request,
    body: ExcludeSalesRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """Persist sale exclusions and recalculate analysis."""
    locale = get_local(request)

    property_obj = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    if not property_obj.asking_price or not property_obj.surface_area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translate("property_needs_price_surface", locale),
        )

    pa = _run_trend_analysis(
        property_obj,
        db,
        locale,
        excluded_sale_ids=body.excluded_sale_ids,
        excluded_neighboring_sale_ids=body.excluded_neighboring_sale_ids,
    )

    # Invalidate cached price analysis
    try:
        r = get_redis()
        r.delete(f"price_analysis_summary:{property_id}", f"price_analysis_full:{property_id}")
    except Exception:
        logger.debug("Failed to invalidate price analysis cache for property %s", property_id)

    return PriceAnalysisFullResponse(**_pa_to_full(pa, False))


@router.get("/{property_id}/market-trend")
async def get_market_trend(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get year-over-year market trend data for visualization.
    Returns cached data from price_analyses if available, otherwise computes fresh.
    """
    locale = get_local(request)

    property_obj = (
        db.query(Property)
        .filter(Property.id == property_id, Property.user_id == int(current_user))
        .first()
    )
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=translate("property_not_found", locale)
        )

    # Try cached
    pa = db.query(PriceAnalysis).filter(PriceAnalysis.property_id == property_obj.id).first()
    if pa and pa.market_trend_json:
        return pa.market_trend_json

    return _compute_market_trend_json(property_obj, db)
