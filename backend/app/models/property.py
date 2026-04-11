"""Property and DVF record models."""

import uuid as uuid_lib
from datetime import datetime

from sqlalchemy import (
    Column,
    Computed,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Property(Base):
    """Property model for storing apartment information."""

    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        String(36), unique=True, index=True, nullable=True, default=lambda: str(uuid_lib.uuid4())
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Address information
    address = Column(String, nullable=False)
    postal_code = Column(String)
    city = Column(String)
    department = Column(String)

    # Property details
    asking_price = Column(Float)
    surface_area = Column(Float)  # in m²
    rooms = Column(Integer)
    property_type = Column(String)  # Appartement, Maison, etc.
    floor = Column(Integer)
    building_floors = Column(Integer)  # Total floors in building (apt) or house
    building_year = Column(Integer)

    # Analysis results
    estimated_value = Column(Float)
    price_per_sqm = Column(Float)
    market_comparison_score = Column(Float)  # 0-100
    recommendation = Column(String)  # "Good deal", "Fair price", "Overpriced", etc.

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="properties")
    documents = relationship(
        "Document", back_populates="related_property", cascade="all, delete-orphan"
    )
    analyses = relationship("Analysis", back_populates="property", cascade="all, delete-orphan")
    price_analysis = relationship(
        "PriceAnalysis", back_populates="property", uselist=False, cascade="all, delete-orphan"
    )


class DVFSale(Base):
    """
    DVF sale record from the geolocalized dataset.

    One row per real estate transaction (~4.8M rows).
    Pre-aggregated from the raw CSV via polars groupby on id_mutation.
    """

    __tablename__ = "dvf_sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_mutation = Column(String, unique=True, nullable=False, index=True)

    # Transaction
    date_mutation = Column(Date, nullable=False, index=True)
    nature_mutation = Column(String)
    prix = Column(Numeric)

    # Address
    adresse_numero = Column(Integer)
    adresse_nom_voie = Column(String)
    adresse_complete = Column(
        String,
        Computed("COALESCE(adresse_numero::text || ' ', '') || adresse_nom_voie", persisted=True),
    )
    code_postal = Column(String(5), index=True)
    code_commune = Column(String(5))
    nom_commune = Column(String)
    code_departement = Column(String(3), index=True)

    # Geolocation
    longitude = Column(Float)
    latitude = Column(Float)

    # Aggregated property info
    type_principal = Column(String)
    surface_bati = Column(Integer)
    nombre_pieces = Column(Integer)
    surface_terrain = Column(Integer)
    nombre_lots = Column(Integer)

    # Counts by type
    n_appartements = Column(SmallInteger)
    n_maisons = Column(SmallInteger)
    n_dependances = Column(SmallInteger)
    n_parcelles_terrain = Column(SmallInteger)

    # Derived
    prix_m2 = Column(Numeric)
    annee = Column(SmallInteger, index=True)

    # Relationship
    lots = relationship("DVFSaleLot", back_populates="sale", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_dvf_sales_postal_type", "code_postal", "type_principal"),
        Index("idx_dvf_sales_postal_type_date", "code_postal", "type_principal", "date_mutation"),
        Index(
            "idx_dvf_sales_adresse_gin",
            "adresse_complete",
            postgresql_using="gin",
            postgresql_ops={"adresse_complete": "gin_trgm_ops"},
        ),
        Index(
            "idx_dvf_sales_prix_m2",
            "prix_m2",
            postgresql_where=Column("prix_m2") > 0,
        ),
    )


class DVFSaleLot(Base):
    """
    Individual lot/component within a DVF sale.

    One row per lot in the raw CSV (~13.5M rows).
    Links back to DVFSale via id_mutation.
    """

    __tablename__ = "dvf_sale_lots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_mutation = Column(
        String, ForeignKey("dvf_sales.id_mutation", ondelete="CASCADE"), nullable=False, index=True
    )

    # Lot details
    lot_type = Column(String, index=True)
    nature_culture = Column(String)
    surface_bati = Column(Integer)
    nombre_pieces = Column(Integer)
    surface_terrain = Column(Integer)

    # Parcel
    id_parcelle = Column(String)

    # Geolocation (per-lot, may differ from sale-level)
    longitude = Column(Float)
    latitude = Column(Float)

    # Relationship
    sale = relationship("DVFSale", back_populates="lots")
