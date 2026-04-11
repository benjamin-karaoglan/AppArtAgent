"""Price analysis persistence model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class PriceAnalysis(Base):
    """Persisted price analysis results for a property."""

    __tablename__ = "price_analyses"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Core metrics
    estimated_value = Column(Float)
    price_per_sqm = Column(Float)
    market_avg_price_per_sqm = Column(Float)
    market_median_price_per_sqm = Column(Float)

    # Analysis results
    price_deviation_percent = Column(Float)
    confidence_score = Column(Float)
    market_trend_annual = Column(Float)
    recommendation = Column(String)
    comparables_count = Column(Integer)

    # Trend projection summary
    estimated_value_2025 = Column(Float)
    projected_price_per_sqm = Column(Float)
    trend_used = Column(Float)
    trend_source = Column(String)
    trend_sample_size = Column(Integer)

    # JSON blobs for full data
    comparable_sales_json = Column(JSON)
    trend_projection_json = Column(JSON)
    market_trend_json = Column(JSON)

    # User exclusions
    excluded_sale_ids = Column(JSON, default=list)
    excluded_neighboring_sale_ids = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    property = relationship("Property", back_populates="price_analysis")
