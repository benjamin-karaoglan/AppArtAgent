"""
Logging and tracing configuration for the application.

Combines standard Python logging with Logfire observability.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import logfire

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured root logger
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler (always available)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handlers (optional - skip if directory is not writable)
    log_dir = Path(os.getenv("LOG_DIR", "/tmp/logs"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)

        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler for all logs
        file_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error file handler
        error_handler = RotatingFileHandler(
            log_dir / "errors.log", maxBytes=10 * 1024 * 1024, backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

        root_logger.info(f"File logging enabled: {log_dir}")
    except (PermissionError, OSError) as e:
        root_logger.warning(f"File logging disabled (permission error): {e}")

    # Set third-party library log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    root_logger.info("=" * 80)
    root_logger.info(f"Logging initialized - Level: {log_level}")
    root_logger.info("=" * 80)

    return root_logger


def setup_logfire(
    service_name: str = "appart-agent",
    environment: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """
    Configure Logfire tracing for observability.

    Args:
        service_name: Name of the service
        environment: Environment name (development, staging, production)
        enable_console: Whether to enable console logging alongside Logfire

    Note: Logfire requires authentication. Set LOGFIRE_TOKEN environment variable
    or run `logfire auth` locally. If not configured, tracing will be disabled.
    """
    # Check if Logfire is enabled and configured
    logfire_token = os.getenv("LOGFIRE_TOKEN", "")
    logfire_enabled = os.getenv("LOGFIRE_ENABLED", "false").lower() == "true"

    if not logfire_enabled and not logfire_token:
        logger.info("Logfire disabled (set LOGFIRE_ENABLED=true or LOGFIRE_TOKEN to enable)")
        return

    try:
        # Enable content capture for GenAI instrumentation
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

        # Set token if provided
        if logfire_token:
            os.environ["LOGFIRE_TOKEN"] = logfire_token

        logfire.configure(
            service_name=service_name,
            service_version="2.0.0",
            environment=environment or os.getenv("ENVIRONMENT", "development"),
            console=logfire.ConsoleOptions(
                colors="auto" if enable_console else "never",
                span_style="show-parents",
                include_timestamps=True,
                verbose=True,
            )
            if enable_console
            else False,
            send_to_logfire=bool(logfire_token) or logfire_enabled,
        )

        # Instrument Google Gemini SDK
        try:
            logfire.instrument_google_genai()
            logger.info("Instrumented Google Gen AI SDK")
        except Exception as e:
            logger.warning(f"Could not instrument Google Gen AI SDK: {e}")

        # Instrument HTTP requests
        try:
            logfire.instrument_httpx()
            logger.info("Instrumented HTTPX")
        except Exception as e:
            logger.warning(f"Could not instrument HTTPX: {e}")

        # Instrument SQLAlchemy
        try:
            logfire.instrument_sqlalchemy()
            logger.info("Instrumented SQLAlchemy")
        except Exception as e:
            logger.warning(f"Could not instrument SQLAlchemy: {e}")

        logger.info("=" * 80)
        logger.info(f"Logfire initialized - Service: {service_name}")
        logger.info(f"Environment: {environment or 'development'}")
        logger.info("=" * 80)

    except Exception as e:
        logger.warning(f"Logfire initialization skipped: {e}")
        logger.info("Continuing without Logfire tracing")


def instrument_fastapi(app) -> None:
    """
    Instrument FastAPI application with Logfire.

    Args:
        app: FastAPI application instance
    """
    try:
        logfire.instrument_fastapi(app)
        logger.info("Instrumented FastAPI app")
    except Exception as e:
        logger.warning(f"Could not instrument FastAPI app: {e}")


# Tracing context managers
def trace_llm_call(model: str, provider: str, operation: str, **kwargs):
    """Context manager for tracing LLM calls."""
    return logfire.span(
        f"llm.{provider}.{operation}", model=model, provider=provider, operation=operation, **kwargs
    )


def trace_storage_operation(operation: str, bucket: str, **kwargs):
    """Context manager for tracing storage operations."""
    return logfire.span(f"storage.{operation}", operation=operation, bucket=bucket, **kwargs)


# Metrics logging
def log_llm_metrics(
    model: str,
    provider: str,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    latency_ms: Optional[int] = None,
    **kwargs,
) -> None:
    """Log LLM usage metrics to Logfire."""
    metrics: dict[str, str | int] = {"model": model, "provider": provider}
    if input_tokens is not None:
        metrics["input_tokens"] = input_tokens
    if output_tokens is not None:
        metrics["output_tokens"] = output_tokens
    if latency_ms is not None:
        metrics["latency_ms"] = latency_ms
    metrics.update(kwargs)
    logfire.info("LLM usage metrics", **metrics)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)
