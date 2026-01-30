"""
Core package - Application configuration, database, security, and logging.

Modules:
- config - Application settings and environment variables
- database - SQLAlchemy database connection and session management
- security - Authentication and password hashing
- logging - Logging and Logfire tracing configuration
"""

from app.core.config import settings
from app.core.database import get_db, SessionLocal, engine
from app.core.logging import (
    setup_logging,
    setup_logfire,
    instrument_fastapi,
    get_logger,
    trace_llm_call,
    trace_storage_operation,
)

__all__ = [
    "settings",
    "get_db",
    "SessionLocal",
    "engine",
    "setup_logging",
    "setup_logfire",
    "instrument_fastapi",
    "get_logger",
    "trace_llm_call",
    "trace_storage_operation",
]
