"""
DVF (Demandes de Valeurs Foncières) service for property price analysis.
"""

import re
import statistics
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.i18n import translate
from app.models.property import DVFSale, Property

# DVF dataset uses abbreviated street types. Map full words → DVF abbreviations.
# Source: frequency analysis of SPLIT_PART(adresse_complete, ' ', 2) in dvf_sales.
_STREET_TYPE_TO_DVF: dict[str, str] = {
    "AVENUE": "AV",
    "BOULEVARD": "BD",
    "ROUTE": "RTE",
    "CHEMIN": "CHE",
    "ALLEE": "ALL",
    "ALLEES": "ALL",
    "IMPASSE": "IMP",
    "PLACE": "PL",
    "RESIDENCE": "RES",
    "COURS": "CRS",
    "SQUARE": "SQ",
    "RUELLE": "RLE",
    "MONTEE": "MTE",
    "PROMENADE": "PROM",
    "TRAVERSE": "TRA",
    "VILLA": "VLA",
    "SENTIER": "SEN",
    "SENTE": "SEN",
    "FAUBOURG": "FG",
    "HAMEAU": "HAM",
    "DOMAINE": "DOM",
    "CORNICHE": "COR",
    "TERRASSE": "TSSE",
    "ESPLANADE": "ESP",
    "CHAUSSEE": "CHS",
    "ROND POINT": "RPT",
    "QUARTIER": "QUA",
    "PASSAGE": "PAS",
    "LOTISSEMENT": "LOT",
}
# Also build reverse map for DVF abbreviation → full word (for matching both ways)
_DVF_TO_STREET_TYPE: dict[str, str] = {v: k for k, v in _STREET_TYPE_TO_DVF.items()}


def normalize_street(name: str) -> str:
    """
    Normalize a street name for fuzzy matching.

    Strips accents, replaces hyphens/apostrophes with spaces, collapses whitespace, uppercases.
    "notre-dame" → "NOTRE DAME"
    "l'église"   → "L EGLISE"
    "  rue   du   parc " → "RUE DU PARC"
    """
    if not name:
        return ""
    # Strip accents: é→e, è→e, ê→e, etc.
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Replace hyphens, apostrophes, dots with space
    ascii_text = re.sub(r"[-''.]+", " ", ascii_text)
    # Collapse whitespace and uppercase
    return re.sub(r"\s+", " ", ascii_text).strip().upper()


def _normalize_street_type(normalized_name: str) -> str:
    """
    Replace full street type words with their DVF abbreviations.

    "BOULEVARD RICHARD WALLACE" → "BD RICHARD WALLACE"
    "AVENUE DE LA CALIFORNIE"   → "AV DE LA CALIFORNIE"

    Handles both single-word types (first word) and multi-word types like "ROND POINT".
    """
    if not normalized_name:
        return normalized_name

    # Check multi-word types first (e.g. "ROND POINT" → "RPT")
    for full, abbr in _STREET_TYPE_TO_DVF.items():
        if " " in full and normalized_name.startswith(full + " "):
            return abbr + normalized_name[len(full) :]

    # Check single-word types (first word only)
    parts = normalized_name.split(" ", 1)
    if parts[0] in _STREET_TYPE_TO_DVF:
        abbr = _STREET_TYPE_TO_DVF[parts[0]]
        return abbr + " " + parts[1] if len(parts) > 1 else abbr

    return normalized_name


def _street_ilike_pattern(street_name: str) -> str:
    """
    Build an ILIKE pattern that matches regardless of hyphens/spaces.
    Also normalizes street types to DVF abbreviations so user input like
    "boulevard richard wallace" matches "BD RICHARD WALLACE" in the DVF dataset.

    "NOTRE DAME" → "NOTRE%DAME" which matches both "NOTRE-DAME" and "NOTRE DAME"
    "BOULEVARD RICHARD WALLACE" → "BD%RICHARD%WALLACE"
    """
    normalized = normalize_street(street_name)
    normalized = _normalize_street_type(normalized)
    # Split on spaces and join with % wildcard
    parts = normalized.split()
    return "%".join(parts)


class DVFService:
    """Service for analyzing DVF data and providing price insights."""

    @staticmethod
    def detect_outliers_iqr(sales: List[DVFSale]) -> List[bool]:
        """
        Detect outliers using the IQR (Interquartile Range) method.

        Outliers are values that fall outside Q1 - 1.5*IQR or Q3 + 1.5*IQR.
        For small datasets (< 4 sales), uses mean ± 2*std deviation instead.
        """
        if len(sales) < 2:
            return [False] * len(sales)

        prices_per_sqm = [float(sale.prix_m2) for sale in sales if sale.prix_m2]

        if len(prices_per_sqm) < 2:
            return [False] * len(sales)

        if len(prices_per_sqm) < 4:
            mean = statistics.mean(prices_per_sqm)
            stdev = statistics.stdev(prices_per_sqm) if len(prices_per_sqm) > 1 else 0
            lower_bound = mean - 1.5 * stdev
            upper_bound = mean + 1.5 * stdev

            outlier_flags = []
            for sale in sales:
                if sale.prix_m2:
                    val = float(sale.prix_m2)
                    is_outlier = val < lower_bound or val > upper_bound
                    outlier_flags.append(is_outlier)
                else:
                    outlier_flags.append(False)
            return outlier_flags

        sorted_prices = sorted(prices_per_sqm)
        q1 = statistics.quantiles(sorted_prices, n=4)[0]
        q3 = statistics.quantiles(sorted_prices, n=4)[2]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_flags = []
        for sale in sales:
            if sale.prix_m2:
                val = float(sale.prix_m2)
                is_outlier = val < lower_bound or val > upper_bound
                outlier_flags.append(is_outlier)
            else:
                outlier_flags.append(False)

        return outlier_flags

    @staticmethod
    def extract_street_info(address: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Extract street number and street name from address.

        Returns:
            Tuple of (street_number, street_name)
        """
        if not address:
            return None, None

        match = re.match(
            r"^(\d+)(?:\s*(?:bis|ter|quater|[A-Z])?)?\s+(.+)$", address.strip(), re.IGNORECASE
        )
        if match:
            try:
                street_number = int(match.group(1))
                street_name = match.group(2).strip().upper()
                return street_number, street_name
            except (ValueError, AttributeError):
                pass

        return None, None

    @staticmethod
    def _build_street_filter(street_name: str, with_number: int | None = None):
        """
        Build an ILIKE filter for adresse_complete that tolerates hyphens/accents.

        If with_number is given: "56 NOTRE%DAME%CHAMPS%"
        Otherwise:               "%NOTRE%DAME%CHAMPS%"
        """
        pattern = _street_ilike_pattern(street_name)
        if with_number is not None:
            return DVFSale.adresse_complete.ilike(f"{with_number} {pattern}%")
        return DVFSale.adresse_complete.ilike(f"%{pattern}%")

    @staticmethod
    def get_exact_address_sales(
        db: Session,
        postal_code: str,
        property_type: str,
        address: str,
        months_back: int = 120,
        max_results: int = 20,
    ) -> List[DVFSale]:
        """
        Get sales for the exact address. Returns one row per transaction.

        Cascade:
        1. Exact number + fuzzy street name
        2. Street name only (no number) within postal code — if number doesn't exist in DVF
        """
        cutoff_date = datetime.now() - timedelta(days=30 * months_back)

        street_number, street_name = DVFService.extract_street_info(address)

        if not street_name:
            return []

        base_filters = and_(
            DVFSale.date_mutation >= cutoff_date,
            DVFSale.type_principal == property_type,
            DVFSale.surface_bati.isnot(None),
            DVFSale.prix_m2.isnot(None),
            DVFSale.prix_m2 > 0,
            DVFSale.code_postal == postal_code,
        )

        # Try exact number + fuzzy street name first
        if street_number:
            query = (
                db.query(DVFSale)
                .filter(
                    base_filters,
                    DVFService._build_street_filter(street_name, with_number=street_number),
                )
                .order_by(DVFSale.date_mutation.desc())
                .limit(max_results)
            )
            results = query.all()
            if results:
                return results

        # Fallback: street name only (number doesn't exist in DVF)
        query = (
            db.query(DVFSale)
            .filter(
                base_filters,
                DVFService._build_street_filter(street_name),
            )
            .order_by(DVFSale.date_mutation.desc())
            .limit(max_results)
        )

        return query.all()

    @staticmethod
    def get_comparable_sales(
        db: Session,
        postal_code: str,
        property_type: str,
        surface_area: float,
        address: str = "",
        radius_km: int = 2,
        months_back: int = 120,
        max_results: int = 20,
    ) -> List[DVFSale]:
        """
        Find comparable property sales from DVF data with smart address-based matching.

        Priority order:
        1. Same exact address (same building)
        2. Neighboring addresses (±2, ±4, ±6, ±8 on same street)
        3. Same street (broader range)
        4. Same postal code (fallback)
        """
        cutoff_date = datetime.now() - timedelta(days=30 * months_back)

        min_surface = surface_area * 0.7
        max_surface = surface_area * 1.3

        street_number, street_name = DVFService.extract_street_info(address)

        base_filters_no_surface = and_(
            DVFSale.date_mutation >= cutoff_date,
            DVFSale.type_principal == property_type,
            DVFSale.surface_bati.isnot(None),
            DVFSale.prix_m2.isnot(None),
            DVFSale.prix_m2 > 0,
            DVFSale.code_postal == postal_code,
        )

        base_filters_with_surface = and_(
            base_filters_no_surface, DVFSale.surface_bati.between(min_surface, max_surface)
        )

        exact_results = []

        if street_number and street_name:
            exact_query = (
                db.query(DVFSale)
                .filter(
                    base_filters_no_surface,
                    DVFService._build_street_filter(street_name, with_number=street_number),
                )
                .order_by(DVFSale.date_mutation.desc())
                .limit(max_results)
            )
            exact_results = exact_query.all()

        # If exact number not found, try street-only within postal code
        if not exact_results and street_name:
            exact_query = (
                db.query(DVFSale)
                .filter(
                    base_filters_no_surface,
                    DVFService._build_street_filter(street_name),
                )
                .order_by(DVFSale.date_mutation.desc())
                .limit(max_results)
            )
            exact_results = exact_query.all()

        if exact_results:
            has_matching_surface = any(
                min_surface <= (sale.surface_bati or 0) <= max_surface for sale in exact_results
            )

            if has_matching_surface or len(exact_results) >= 3:
                return exact_results[:max_results]

            results = list(exact_results)
        else:
            results = []

        # Priority 2: Neighboring addresses
        if street_number and street_name:
            neighbors = []
            for offset in [2, 4, 6, 8, 10]:
                neighbors.append(street_number + offset)
                if street_number - offset > 0:
                    neighbors.append(street_number - offset)

            neighbor_conditions = [
                DVFService._build_street_filter(street_name, with_number=num) for num in neighbors
            ]

            neighbor_query = (
                db.query(DVFSale)
                .filter(base_filters_with_surface, or_(*neighbor_conditions))
                .order_by(DVFSale.date_mutation.desc())
                .limit(max_results - len(results))
            )

            neighbor_results = neighbor_query.all()
            existing_ids = {r.id for r in results}
            results.extend([r for r in neighbor_results if r.id not in existing_ids])

        # Priority 3: Same street
        if len(results) < 5 and street_name:
            street_query = (
                db.query(DVFSale)
                .filter(base_filters_with_surface, DVFService._build_street_filter(street_name))
                .order_by(DVFSale.date_mutation.desc())
                .limit(max_results - len(results))
            )

            street_results = street_query.all()
            existing_ids = {r.id for r in results}
            results.extend([r for r in street_results if r.id not in existing_ids])

        # Priority 4: Same postal code
        if len(results) < 5:
            fallback_query = (
                db.query(DVFSale)
                .filter(base_filters_with_surface)
                .order_by(DVFSale.date_mutation.desc())
                .limit(max_results - len(results))
            )

            fallback_results = fallback_query.all()
            existing_ids = {r.id for r in results}
            results.extend([r for r in fallback_results if r.id not in existing_ids])

        # Sort: exact address first, then others by date
        if exact_results:
            exact_ids = {r.id for r in exact_results}
            exact_list = [r for r in results if r.id in exact_ids]
            non_exact_list = [r for r in results if r.id not in exact_ids]

            exact_list.sort(key=lambda x: x.date_mutation, reverse=True)
            non_exact_list.sort(key=lambda x: x.date_mutation, reverse=True)

            results = exact_list + non_exact_list
        else:
            results.sort(key=lambda x: x.date_mutation, reverse=True)

        return results[:max_results]

    @staticmethod
    def get_neighboring_sales_for_trend(
        db: Session,
        postal_code: str,
        property_type: str,
        months_back: int = 60,
        max_results: int = 500,
    ) -> List[DVFSale]:
        """
        Get postal-code-level sales for trend calculation.
        Uses all sales in the postal code for the given property type.
        NO surface area filter - we want all sales for accurate trends.
        """
        cutoff_date = datetime.now() - timedelta(days=30 * months_back)

        query = (
            db.query(DVFSale)
            .filter(
                DVFSale.date_mutation >= cutoff_date,
                DVFSale.type_principal == property_type,
                DVFSale.surface_bati.isnot(None),
                DVFSale.prix_m2.isnot(None),
                DVFSale.prix_m2 > 0,
                DVFSale.code_postal == postal_code,
            )
            .order_by(DVFSale.date_mutation.desc())
            .limit(max_results)
        )

        return query.all()

    @staticmethod
    def calculate_market_trend(
        comparable_sales: List[DVFSale],
    ) -> Dict[str, Any]:
        """
        Calculate market trend using linear regression on yearly median EUR/m2.

        Returns:
            Dict with trend_pct, r_squared, sample_size, years_count, confidence_level
        """
        insufficient = {
            "trend_pct": 0.0,
            "r_squared": 0.0,
            "sample_size": len(comparable_sales),
            "years_count": 0,
            "confidence_level": "low",
        }

        if len(comparable_sales) < 2:
            return insufficient

        sales_by_year: dict[int, list[float]] = {}
        for sale in comparable_sales:
            sale_date = getattr(sale, "date_mutation", None) or getattr(sale, "sale_date", None)
            prix_m2 = getattr(sale, "prix_m2", None) or getattr(sale, "price_per_sqm", None)
            if sale_date and prix_m2 and float(prix_m2) > 0:
                year = sale_date.year
                if year not in sales_by_year:
                    sales_by_year[year] = []
                sales_by_year[year].append(float(prix_m2))

        if len(sales_by_year) < 2:
            return insufficient

        year_medians = {year: statistics.median(prices) for year, prices in sales_by_year.items()}
        sorted_years = sorted(year_medians.keys())
        years_array = np.array(sorted_years, dtype=float)
        medians_array = np.array([year_medians[y] for y in sorted_years], dtype=float)

        # Linear regression: median_price = slope * year + intercept
        coeffs = np.polyfit(years_array, medians_array, 1)
        slope = coeffs[0]

        # R-squared calculation
        predicted = np.polyval(coeffs, years_array)
        ss_res = np.sum((medians_array - predicted) ** 2)
        ss_tot = np.sum((medians_array - np.mean(medians_array)) ** 2)
        r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Convert slope to annual percentage relative to latest year median
        latest_median = year_medians[sorted_years[-1]]
        trend_pct = (slope / latest_median) * 100 if latest_median > 0 else 0.0

        sample_size = len(comparable_sales)
        years_count = len(sales_by_year)

        # Confidence level
        if r_squared >= 0.7 and sample_size >= 50 and years_count >= 4:
            confidence_level = "high"
        elif r_squared >= 0.4 and sample_size >= 20 and years_count >= 3:
            confidence_level = "moderate"
        else:
            confidence_level = "low"

        return {
            "trend_pct": float(round(trend_pct, 2)),
            "r_squared": float(round(r_squared, 4)),
            "sample_size": sample_size,
            "years_count": years_count,
            "confidence_level": confidence_level,
        }

    @staticmethod
    def apply_time_adjustment(
        price_per_sqm: float, sale_date: Union[datetime, date], trend_pct: float
    ) -> float:
        """Adjust historical price to current value using trend."""
        if not sale_date or trend_pct == 0:
            return price_per_sqm

        if isinstance(sale_date, date) and not isinstance(sale_date, datetime):
            sale_datetime = datetime.combine(sale_date, datetime.min.time())
        else:
            sale_datetime = sale_date

        years_diff = (datetime.now() - sale_datetime).days / 365.25

        adjustment_factor = (1 + trend_pct / 100) ** years_diff

        return float(price_per_sqm * adjustment_factor)

    @staticmethod
    def calculate_trend_based_projection(
        exact_address_sales: List[DVFSale],
        neighboring_sales: List[DVFSale],
        surface_area: float,
    ) -> Dict[str, Any]:
        """
        Calculate price projection using trend from neighboring addresses.
        """
        if not exact_address_sales or not neighboring_sales:
            return {
                "estimated_value_2025": None,
                "trend_used": 0,
                "trend_source": "insufficient_data",
                "base_sale_date": None,
                "base_price_per_sqm": None,
                "confidence_level": "low",
            }

        # Get most recent exact address sale
        exact_address_sales.sort(
            key=lambda x: getattr(x, "date_mutation", None) or getattr(x, "sale_date", None),
            reverse=True,
        )
        base_sale = exact_address_sales[0]
        base_date = getattr(base_sale, "date_mutation", None) or getattr(
            base_sale, "sale_date", None
        )
        base_prix_m2 = float(
            getattr(base_sale, "prix_m2", None) or getattr(base_sale, "price_per_sqm", None) or 0
        )

        trend_result = DVFService.calculate_market_trend(neighboring_sales)
        trend_pct = trend_result["trend_pct"]

        if abs(trend_pct) < 0.1:
            return {
                "estimated_value_2025": base_prix_m2 * surface_area,
                "trend_used": 0,
                "trend_source": "no_significant_trend",
                "base_sale_date": base_date,
                "base_price_per_sqm": base_prix_m2,
                "confidence_level": trend_result["confidence_level"],
            }

        projected_price_per_sqm = DVFService.apply_time_adjustment(
            base_prix_m2, base_date, trend_pct
        )

        return {
            "estimated_value_2025": projected_price_per_sqm * surface_area,
            "projected_price_per_sqm": projected_price_per_sqm,
            "trend_used": trend_pct,
            "trend_source": "postal_code_regression",
            "base_sale_date": base_date,
            "base_price_per_sqm": base_prix_m2,
            "trend_sample_size": trend_result["sample_size"],
            "confidence_level": trend_result["confidence_level"],
        }

    @staticmethod
    def calculate_price_analysis(
        asking_price: float,
        surface_area: float,
        comparable_sales: List[DVFSale],
        exclude_indices: Optional[List[int]] = None,
        apply_time_adjustment: bool = False,
        locale: str = "fr",
    ) -> Dict[str, Any]:
        """Calculate comprehensive price analysis based on comparable sales."""
        if not comparable_sales:
            return {
                "estimated_value": asking_price,
                "price_per_sqm": asking_price / surface_area if surface_area else 0,
                "market_avg_price_per_sqm": 0,
                "price_deviation_percent": 0,
                "recommendation": translate("insufficient_data", locale),
                "confidence_score": 0,
                "market_trend_annual": 0,
            }

        exclude_set = set(exclude_indices or [])
        filtered_sales = [sale for i, sale in enumerate(comparable_sales) if i not in exclude_set]

        if not filtered_sales:
            return {
                "estimated_value": asking_price,
                "price_per_sqm": asking_price / surface_area if surface_area else 0,
                "market_avg_price_per_sqm": 0,
                "price_deviation_percent": 0,
                "recommendation": translate("insufficient_data_excluded", locale),
                "confidence_score": 0,
                "market_trend_annual": 0,
            }

        market_trend_result = DVFService.calculate_market_trend(filtered_sales)
        market_trend = market_trend_result["trend_pct"]

        adjusted_prices = []
        for sale in filtered_sales:
            prix_m2 = getattr(sale, "prix_m2", None) or getattr(sale, "price_per_sqm", None)
            if prix_m2 and float(prix_m2) > 0:
                sale_date = getattr(sale, "date_mutation", None) or getattr(sale, "sale_date", None)
                if apply_time_adjustment and abs(market_trend) > 0.5:
                    adjusted_price = DVFService.apply_time_adjustment(
                        float(prix_m2), sale_date, market_trend
                    )
                else:
                    adjusted_price = float(prix_m2)
                adjusted_prices.append(adjusted_price)

        if not adjusted_prices:
            return {
                "estimated_value": asking_price,
                "price_per_sqm": asking_price / surface_area if surface_area else 0,
                "market_avg_price_per_sqm": 0,
                "price_deviation_percent": 0,
                "recommendation": translate("insufficient_data", locale),
                "confidence_score": 0,
                "market_trend_annual": 0,
            }

        market_avg_price_per_sqm = statistics.mean(adjusted_prices)
        market_median_price_per_sqm = statistics.median(adjusted_prices)

        estimated_value = market_avg_price_per_sqm * surface_area
        asking_price_per_sqm = asking_price / surface_area if surface_area else 0

        price_deviation_percent = (
            ((asking_price_per_sqm - market_avg_price_per_sqm) / market_avg_price_per_sqm) * 100
            if market_avg_price_per_sqm > 0
            else 0
        )

        if price_deviation_percent < -10:
            recommendation = translate("excellent_deal", locale)
        elif price_deviation_percent < -5:
            recommendation = translate("good_deal", locale)
        elif price_deviation_percent < 5:
            recommendation = translate("fair_price", locale)
        elif price_deviation_percent < 10:
            recommendation = translate("slightly_overpriced", locale)
        elif price_deviation_percent < 20:
            recommendation = translate("overpriced", locale)
        else:
            recommendation = translate("heavily_overpriced", locale)

        confidence_score = min(100, (len(filtered_sales) / 20) * 100)

        return {
            "estimated_value": round(estimated_value, 2),
            "price_per_sqm": round(asking_price_per_sqm, 2),
            "market_avg_price_per_sqm": round(market_avg_price_per_sqm, 2),
            "market_median_price_per_sqm": round(market_median_price_per_sqm, 2),
            "price_deviation_percent": round(price_deviation_percent, 2),
            "recommendation": recommendation,
            "confidence_score": round(confidence_score, 2),
            "comparables_count": len(filtered_sales),
            "market_trend_annual": round(market_trend, 2),
        }

    @staticmethod
    def calculate_investment_score(
        property_data: Property,
        price_analysis: Dict[str, Any],
        annual_costs: float,
        risk_factors: List[str],
    ) -> Dict[str, Any]:
        """Calculate overall investment score and metrics."""
        price_deviation = price_analysis.get("price_deviation_percent", 0)
        if price_deviation < -10:
            value_score = 100
        elif price_deviation < 0:
            value_score = 80 + (abs(price_deviation) * 2)
        elif price_deviation < 10:
            value_score = 70 - (price_deviation * 3)
        else:
            value_score = max(0, 50 - (price_deviation - 10) * 2)

        risk_penalty = len(risk_factors) * 15
        risk_score = max(0, 100 - risk_penalty)

        if property_data.asking_price:
            cost_ratio = (annual_costs / property_data.asking_price) * 100
            if cost_ratio < 2:
                cost_score = 100
            elif cost_ratio < 3:
                cost_score = 80
            elif cost_ratio < 4:
                cost_score = 60
            else:
                cost_score = max(0, 50 - (cost_ratio - 4) * 10)
        else:
            cost_score = 50

        investment_score = value_score * 0.4 + risk_score * 0.3 + cost_score * 0.3

        if investment_score >= 80:
            overall_recommendation = "Highly Recommended"
        elif investment_score >= 65:
            overall_recommendation = "Recommended with minor reservations"
        elif investment_score >= 50:
            overall_recommendation = "Proceed with caution"
        else:
            overall_recommendation = "Not recommended"

        return {
            "investment_score": round(investment_score, 2),
            "value_score": round(value_score, 2),
            "risk_score": round(risk_score, 2),
            "cost_score": round(cost_score, 2),
            "overall_recommendation": overall_recommendation,
        }


# Singleton instance
dvf_service = DVFService()
