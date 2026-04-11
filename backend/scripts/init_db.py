#!/usr/bin/env python3
"""
Automatic database initialization script.
Runs migrations on startup and creates a test user for development.
"""

import logging
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text

from app.core.database import SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_db(max_retries=30):
    """Wait for database to be ready."""
    logger.info("Waiting for database to be ready...")

    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Database is ready")
            return True
        except Exception as e:
            if i < max_retries - 1:
                logger.info(f"Database not ready yet, waiting... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                logger.error(f"Database not ready after {max_retries} attempts: {e}")
                return False

    return False


def check_tables_exist():
    """Check if database tables exist."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        required_tables = ["users", "properties", "documents", "dvf_sales"]

        missing_tables = [t for t in required_tables if t not in tables]

        if missing_tables:
            logger.info(f"Missing tables: {missing_tables}")
            return False
        else:
            logger.info(f"✓ All required tables exist ({len(tables)} total)")
            return True
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False


def run_migrations():
    """Run Alembic migrations."""
    logger.info("Running database migrations...")

    try:
        import subprocess

        result = subprocess.run(
            ["alembic", "upgrade", "head"], cwd="/app", capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            logger.info("✓ Migrations completed successfully")
            logger.debug(result.stdout)
            return True
        else:
            logger.error(f"Migration failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False


def create_test_user():
    """Create a default test user if none exists."""
    logger.info("Checking for test user...")

    try:
        from app.core.security import get_password_hash
        from app.models.user import User

        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == "test@example.com").first()

            if not existing:
                user = User(
                    email="test@example.com",
                    hashed_password=get_password_hash("test123"),
                    full_name="Test User",
                    is_active=True,
                    is_superuser=False,
                )
                db.add(user)
                db.commit()
                logger.info("✓ Test user created (email: test@example.com, password: test123)")
            else:
                logger.info("✓ Test user already exists")

            return True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        return False


def main():
    """Main initialization function."""
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)

    # Step 1: Wait for database
    if not wait_for_db():
        logger.error("Failed to connect to database")
        sys.exit(1)

    # Step 2: Check if tables exist
    tables_exist = check_tables_exist()

    # Step 3: Run migrations if needed
    if not tables_exist:
        logger.info("Tables missing, running migrations...")
        if not run_migrations():
            logger.error("Migration failed")
            sys.exit(1)
    else:
        logger.info("Tables exist, checking if migrations are needed...")
        run_migrations()  # Run anyway to ensure we're up to date

    # Step 4: Create test user
    create_test_user()

    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION COMPLETE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("You can now:")
    logger.info("  - Access frontend: http://localhost:3000")
    logger.info("  - Login with: test@example.com / test123")
    logger.info("  - Access MinIO Console: http://localhost:9001 (minioadmin/minioadmin)")
    logger.info("")
    logger.info("To import DVF data, run: uv run import-dvf")
    logger.info("")


if __name__ == "__main__":
    main()
