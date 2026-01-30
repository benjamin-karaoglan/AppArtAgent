"""
Price Analysis - DVF-based property price analysis.

Analyzes French property prices using DVF (Demandes de Valeurs Foncières) data.
This module provides market analysis, comparable sales, and price trends.

Re-exports from dvf_service for backward compatibility and cleaner naming.
"""

# Import everything from dvf_service for backward compatibility
from app.services.dvf_service import DVFService

# Create aliases with cleaner names
PriceAnalyzer = DVFService
price_analyzer = DVFService  # Alias for consistency


def get_price_analyzer() -> DVFService:
    """Get a DVFService instance for price analysis."""
    return DVFService()


# Backward compatibility
get_dvf_service = get_price_analyzer
