#!/usr/bin/env python3
"""
Migration script for Cloud Run Jobs.
Runs alembic migrations with proper error handling and logging.
"""

import os
import subprocess
import sys


def main():
    print("=" * 60)
    print("Starting database migration...")
    print("=" * 60)

    # Check DATABASE_URL is set
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        sys.exit(1)

    # Mask password in output
    masked_url = db_url
    if "@" in db_url and ":" in db_url:
        # postgresql://user:password@host -> postgresql://user:***@host
        parts = db_url.split("@")
        if len(parts) >= 2:
            user_pass = parts[0].rsplit(":", 1)
            if len(user_pass) == 2:
                masked_url = f"{user_pass[0]}:***@{'@'.join(parts[1:])}"

    print(f"DATABASE_URL: {masked_url}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")

    # Test imports
    print("\nTesting imports...")
    try:
        import sqlalchemy

        print(f"  SQLAlchemy: {sqlalchemy.__version__}")
        import alembic

        print(f"  Alembic: {alembic.__version__}")
        import psycopg2

        print(f"  psycopg2: {psycopg2.__version__}")
    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        sys.exit(1)

    # Test database connection
    print("\nTesting database connection...")
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"  Connection successful! Result: {result.fetchone()}")
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        sys.exit(1)

    # Run alembic
    print("\nRunning alembic upgrade head...")
    print("-" * 60)

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="/app",
        capture_output=False,  # Show output in real-time
        env=os.environ,
    )

    print("-" * 60)

    if result.returncode != 0:
        print(f"ERROR: Alembic failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
