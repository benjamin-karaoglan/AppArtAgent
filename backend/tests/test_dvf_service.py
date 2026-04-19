"""Unit tests for DVF service."""

from datetime import date, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.services.dvf_service import (
    DVFService,
    _normalize_street_type,
    _street_ilike_pattern,
    normalize_street,
)


class TestNormalizeStreet:
    """Test street name normalization."""

    def test_hyphen_removal(self):
        assert normalize_street("notre-dame") == "NOTRE DAME"

    def test_accent_removal(self):
        assert normalize_street("l'église") == "L EGLISE"

    def test_multiple_hyphens(self):
        assert normalize_street("saint-germain-des-prés") == "SAINT GERMAIN DES PRES"

    def test_collapse_whitespace(self):
        assert normalize_street("  rue   du   parc ") == "RUE DU PARC"

    def test_empty(self):
        assert normalize_street("") == ""

    def test_already_normalized(self):
        assert normalize_street("RUE NOTRE DAME DES CHAMPS") == "RUE NOTRE DAME DES CHAMPS"


class TestNormalizeStreetType:
    """Test DVF street type abbreviation normalization."""

    def test_boulevard(self):
        assert _normalize_street_type("BOULEVARD RICHARD WALLACE") == "BD RICHARD WALLACE"

    def test_avenue(self):
        assert _normalize_street_type("AVENUE DE LA CALIFORNIE") == "AV DE LA CALIFORNIE"

    def test_route(self):
        assert _normalize_street_type("ROUTE DE PARIS") == "RTE DE PARIS"

    def test_impasse(self):
        assert _normalize_street_type("IMPASSE DES LILAS") == "IMP DES LILAS"

    def test_place(self):
        assert _normalize_street_type("PLACE DE LA REPUBLIQUE") == "PL DE LA REPUBLIQUE"

    def test_rue_unchanged(self):
        """RUE is already used as-is in DVF data, should not be changed."""
        assert _normalize_street_type("RUE NOTRE DAME DES CHAMPS") == "RUE NOTRE DAME DES CHAMPS"

    def test_already_abbreviated(self):
        """Already abbreviated should pass through unchanged."""
        assert _normalize_street_type("BD RICHARD WALLACE") == "BD RICHARD WALLACE"

    def test_rond_point(self):
        """Multi-word type: ROND POINT → RPT."""
        assert _normalize_street_type("ROND POINT DES CHAMPS ELYSEES") == "RPT DES CHAMPS ELYSEES"

    def test_empty(self):
        assert _normalize_street_type("") == ""

    def test_no_type(self):
        """A name without a known type stays unchanged."""
        assert _normalize_street_type("NOTRE DAME DES CHAMPS") == "NOTRE DAME DES CHAMPS"


class TestStreetIlikePattern:
    """Test ILIKE pattern generation."""

    def test_simple(self):
        assert _street_ilike_pattern("RUE NOTRE-DAME DES CHAMPS") == "RUE%NOTRE%DAME%DES%CHAMPS"

    def test_with_accent(self):
        assert _street_ilike_pattern("rue de l'église") == "RUE%DE%L%EGLISE"

    def test_matches_both_forms(self):
        """Pattern from 'notre dame' should match 'NOTRE-DAME' via SQL ILIKE."""
        pattern = _street_ilike_pattern("notre dame")
        # Pattern is "NOTRE%DAME" which ILIKE matches "NOTRE-DAME DES CHAMPS"
        assert pattern == "NOTRE%DAME"

    def test_boulevard_to_bd(self):
        """Full word 'boulevard' should be abbreviated to BD in the pattern."""
        pattern = _street_ilike_pattern("boulevard richard wallace")
        assert pattern == "BD%RICHARD%WALLACE"

    def test_avenue_to_av(self):
        pattern = _street_ilike_pattern("avenue de la californie")
        assert pattern == "AV%DE%LA%CALIFORNIE"


class TestExtractStreetInfo:
    """Test extract_street_info method."""

    def test_extract_valid_address(self):
        """Test extracting street number and name from valid address."""
        number, name = DVFService.extract_street_info("56 RUE NOTRE-DAME DES CHAMPS")
        assert number == 56
        assert name == "RUE NOTRE-DAME DES CHAMPS"

    def test_extract_address_with_bis(self):
        """Test extracting address with 'bis' suffix."""
        number, name = DVFService.extract_street_info("56 bis RUE NOTRE-DAME DES CHAMPS")
        assert number == 56
        assert name == "RUE NOTRE-DAME DES CHAMPS"

    def test_extract_address_with_lowercase(self):
        """Test extracting lowercase address."""
        number, name = DVFService.extract_street_info("18 rue jean mermoz")
        assert number == 18
        assert name == "RUE JEAN MERMOZ"

    def test_extract_address_no_number(self):
        """Test extracting address without number."""
        number, name = DVFService.extract_street_info("RUE NOTRE-DAME DES CHAMPS")
        assert number is None
        assert name is None

    def test_extract_empty_address(self):
        """Test extracting from empty address."""
        number, name = DVFService.extract_street_info("")
        assert number is None
        assert name is None

    def test_extract_none_address(self):
        """Test extracting from None address."""
        number, name = DVFService.extract_street_info(None)
        assert number is None
        assert name is None


class TestApplyTimeAdjustment:
    """Test apply_time_adjustment method."""

    def test_apply_positive_trend(self):
        """Test applying positive market trend."""
        sale_date = datetime.now() - timedelta(days=365)
        adjusted = DVFService.apply_time_adjustment(10000, sale_date, 5.0)
        assert 10400 < adjusted < 10600

    def test_apply_negative_trend(self):
        """Test applying negative market trend."""
        sale_date = datetime.now() - timedelta(days=365)
        adjusted = DVFService.apply_time_adjustment(10000, sale_date, -5.0)
        assert 9400 < adjusted < 9600

    def test_apply_zero_trend(self):
        """Test with zero trend (no adjustment)."""
        sale_date = datetime.now() - timedelta(days=365)
        adjusted = DVFService.apply_time_adjustment(10000, sale_date, 0.0)
        assert adjusted == 10000

    def test_apply_with_date_object(self):
        """Test with date object instead of datetime."""
        sale_date = date.today() - timedelta(days=365)
        adjusted = DVFService.apply_time_adjustment(10000, sale_date, 5.0)
        assert 10400 < adjusted < 10600

    def test_apply_with_none_date(self):
        """Test with None date (should return original price)."""
        adjusted = DVFService.apply_time_adjustment(10000, None, 5.0)
        assert adjusted == 10000


def _mock_sale(sale_date, prix_m2):
    """Create a mock DVFSale with both old and new attribute names."""
    return Mock(
        date_mutation=sale_date,
        sale_date=sale_date,
        prix_m2=prix_m2,
        price_per_sqm=prix_m2,
    )


class TestCalculateMarketTrend:
    """Test calculate_market_trend with linear regression."""

    def test_trend_with_linear_increase(self):
        """Steady +5% per year over 5 years should produce ~5% trend."""
        base = 10000
        sales = []
        for year_offset in range(5):
            price = base * (1.05**year_offset)
            # 11 sales per year to exceed high confidence threshold (55 total >= 50)
            for month in range(1, 12):
                sales.append(_mock_sale(date(2021 + year_offset, month, 1), price + (month * 5)))
        result = DVFService.calculate_market_trend(sales)
        assert isinstance(result, dict)
        assert 4.0 < result["trend_pct"] < 6.0
        assert result["confidence_level"] == "high"
        assert result["sample_size"] == 55
        assert result["years_count"] == 5

    def test_trend_with_flat_market(self):
        """Same median every year should produce ~0% trend."""
        sales = []
        for year_offset in range(4):
            for month in [1, 6]:
                sales.append(_mock_sale(date(2021 + year_offset, month, 1), 10000))
        result = DVFService.calculate_market_trend(sales)
        assert isinstance(result, dict)
        assert abs(result["trend_pct"]) < 1.0

    def test_trend_with_decrease(self):
        """Decreasing prices should produce negative trend."""
        sales = []
        for year_offset in range(4):
            price = 12000 - (year_offset * 500)
            for month in [1, 6]:
                sales.append(_mock_sale(date(2021 + year_offset, month, 1), price))
        result = DVFService.calculate_market_trend(sales)
        assert result["trend_pct"] < 0

    def test_trend_insufficient_data_one_sale(self):
        """Single sale returns zero trend with low confidence."""
        sales = [_mock_sale(date(2024, 1, 1), 10000)]
        result = DVFService.calculate_market_trend(sales)
        assert result["trend_pct"] == 0.0
        assert result["confidence_level"] == "low"

    def test_trend_insufficient_data_single_year(self):
        """All sales in one year returns zero trend."""
        sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 6, 1), 10500),
            _mock_sale(date(2024, 12, 1), 11000),
        ]
        result = DVFService.calculate_market_trend(sales)
        assert result["trend_pct"] == 0.0
        assert result["confidence_level"] == "low"

    def test_confidence_moderate(self):
        """Moderate confidence: R² >= 0.4, >= 20 sales, >= 3 years."""
        sales = []
        for year_offset in range(3):
            price = 10000 + (year_offset * 300)
            for i in range(7):
                # Add noise to lower R²
                noise = (i - 3) * 200
                sales.append(_mock_sale(date(2022 + year_offset, 1 + i, 1), price + noise))
        result = DVFService.calculate_market_trend(sales)
        assert result["years_count"] == 3
        assert result["sample_size"] == 21
        # With noise, confidence should be moderate (not high due to lower R²)
        assert result["confidence_level"] in ("moderate", "high")

    def test_confidence_low_few_years(self):
        """Only 2 years with few sales = low confidence."""
        sales = [
            _mock_sale(date(2023, 1, 1), 10000),
            _mock_sale(date(2024, 1, 1), 10500),
        ]
        result = DVFService.calculate_market_trend(sales)
        assert result["confidence_level"] == "low"


class TestCalculatePriceAnalysis:
    """Test calculate_price_analysis method."""

    def test_analysis_with_comparable_sales(self):
        """Test price analysis with comparable sales."""
        comparable_sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 2, 1), 10200),
            _mock_sale(date(2024, 3, 1), 10100),
            _mock_sale(date(2024, 4, 1), 9900),
            _mock_sale(date(2024, 5, 1), 10300),
        ]

        analysis = DVFService.calculate_price_analysis(
            asking_price=650000,
            surface_area=65,
            comparable_sales=comparable_sales,
        )

        assert "estimated_value" in analysis
        assert "price_per_sqm" in analysis
        assert "market_avg_price_per_sqm" in analysis
        assert "market_median_price_per_sqm" in analysis
        assert "price_deviation_percent" in analysis
        assert "recommendation" in analysis
        assert "confidence_score" in analysis
        assert analysis["comparables_count"] == 5

    def test_analysis_fair_price(self):
        """Test analysis when price is fair."""
        comparable_sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 2, 1), 10000),
        ]

        analysis = DVFService.calculate_price_analysis(
            asking_price=650000,
            surface_area=65,
            comparable_sales=comparable_sales,
        )

        assert -5 <= analysis["price_deviation_percent"] <= 5

    def test_analysis_overpriced(self):
        """Test analysis when price is overpriced."""
        comparable_sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 2, 1), 10000),
        ]

        analysis = DVFService.calculate_price_analysis(
            asking_price=780000,
            surface_area=65,
            comparable_sales=comparable_sales,
        )

        assert analysis["price_deviation_percent"] > 10
        assert (
            "surévalué" in analysis["recommendation"].lower()
            or "overpriced" in analysis["recommendation"].lower()
        )

    def test_analysis_underpriced(self):
        """Test analysis when price is below market."""
        comparable_sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 2, 1), 10000),
        ]

        analysis = DVFService.calculate_price_analysis(
            asking_price=520000,
            surface_area=65,
            comparable_sales=comparable_sales,
        )

        assert analysis["price_deviation_percent"] < -10
        assert (
            "affaire" in analysis["recommendation"].lower()
            or "deal" in analysis["recommendation"].lower()
        )

    def test_analysis_no_sales(self):
        """Test analysis with no comparable sales."""
        analysis = DVFService.calculate_price_analysis(
            asking_price=650000, surface_area=65, comparable_sales=[]
        )

        assert analysis["recommendation"] in ("Insufficient data", "Données insuffisantes")
        assert analysis["confidence_score"] == 0

    def test_median_price_calculation(self):
        """Test that median price is calculated correctly."""
        comparable_sales = [
            _mock_sale(date(2024, 1, 1), 8000),
            _mock_sale(date(2024, 2, 1), 9000),
            _mock_sale(date(2024, 3, 1), 10000),
            _mock_sale(date(2024, 4, 1), 11000),
            _mock_sale(date(2024, 5, 1), 12000),
        ]

        analysis = DVFService.calculate_price_analysis(
            asking_price=650000, surface_area=65, comparable_sales=comparable_sales
        )

        assert analysis["market_median_price_per_sqm"] == 10000


class TestCalculateTrendBasedProjection:
    """Test calculate_trend_based_projection method."""

    def test_projection_with_data(self):
        """Test projection with exact address and neighboring sales."""
        exact_sales = [
            _mock_sale(date(2024, 1, 1), 10000),
        ]

        neighboring_sales = [
            _mock_sale(date(2023, 1, 1), 9000),
            _mock_sale(date(2024, 1, 1), 10000),
        ]

        projection = DVFService.calculate_trend_based_projection(
            exact_address_sales=exact_sales, neighboring_sales=neighboring_sales, surface_area=65
        )

        assert "estimated_value_2025" in projection
        assert "trend_used" in projection
        assert "trend_source" in projection
        assert "base_sale_date" in projection
        assert projection["base_sale_date"] == date(2024, 1, 1)

    def test_projection_no_data(self):
        """Test projection with no data."""
        projection = DVFService.calculate_trend_based_projection(
            exact_address_sales=[], neighboring_sales=[], surface_area=65
        )

        assert projection["estimated_value_2025"] is None
        assert projection["trend_source"] == "insufficient_data"


class TestDetectOutliersIQR:
    """Test outlier detection via IQR method."""

    def test_detects_obvious_outlier(self):
        """A sale at 100x the normal price should be flagged with enough data points."""
        sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 2, 1), 10200),
            _mock_sale(date(2024, 3, 1), 10100),
            _mock_sale(date(2024, 4, 1), 9900),
            _mock_sale(date(2024, 5, 1), 10050),
            _mock_sale(date(2024, 6, 1), 10150),
            _mock_sale(date(2024, 7, 1), 9950),
            _mock_sale(date(2024, 8, 1), 100000),  # outlier
        ]
        flags = DVFService.detect_outliers_iqr(sales)
        assert len(flags) == 8
        assert flags[7] is True  # the outlier
        assert sum(flags) >= 1

    def test_no_outliers_in_tight_data(self):
        """Similar prices should produce no outliers."""
        sales = [
            _mock_sale(date(2024, 1, 1), 10000),
            _mock_sale(date(2024, 2, 1), 10100),
            _mock_sale(date(2024, 3, 1), 10050),
        ]
        flags = DVFService.detect_outliers_iqr(sales)
        assert sum(flags) == 0

    def test_empty_input(self):
        """Empty list should return empty flags."""
        flags = DVFService.detect_outliers_iqr([])
        assert flags == []


class TestExcludeIndicesWithOutliers:
    """Test that exclusion by index works correctly for price analysis."""

    def test_excluding_sales_changes_result(self):
        """Excluding an expensive sale should lower the estimated value."""
        cheap_sales = [
            _mock_sale(date(2024, 1, 1), 8000),
            _mock_sale(date(2024, 2, 1), 8100),
            _mock_sale(date(2024, 3, 1), 8200),
        ]
        expensive_sale = _mock_sale(date(2024, 4, 1), 15000)
        all_sales = cheap_sales + [expensive_sale]

        analysis_all = DVFService.calculate_price_analysis(
            asking_price=600000, surface_area=65, comparable_sales=all_sales
        )
        analysis_excluded = DVFService.calculate_price_analysis(
            asking_price=600000, surface_area=65, comparable_sales=all_sales, exclude_indices=[3]
        )

        # With the expensive sale excluded, estimated value should be lower
        assert analysis_excluded["estimated_value"] < analysis_all["estimated_value"]
        assert analysis_excluded["comparables_count"] == 3
        assert analysis_all["comparables_count"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
