#!/bin/bash
# Production startup script - Run migrations then start server
# Used by Cloud Run and production Docker deployments

echo "=============================================="
echo "PRODUCTION STARTUP"
echo "=============================================="
echo "Starting at $(date)"

# Function to run migrations with retries
run_migrations() {
    local max_attempts=5
    local attempt=1
    local wait_time=5
    
    while [ $attempt -le $max_attempts ]; do
        echo "Migration attempt $attempt of $max_attempts..."
        
        # Test database connection
        python -c "
import os
import sys
from sqlalchemy import create_engine, text

db_url = os.environ.get('DATABASE_URL', '')
if not db_url:
    print('ERROR: DATABASE_URL not set')
    sys.exit(1)

# Mask password for logging
masked = db_url
if '@' in db_url:
    parts = db_url.split('@')
    user_part = parts[0].rsplit(':', 1)
    if len(user_part) == 2:
        masked = f'{user_part[0]}:***@{\"@\".join(parts[1:])}'
print(f'Database URL: {masked}')

# Test connection
print('Testing database connection...')
try:
    engine = create_engine(db_url, connect_args={'connect_timeout': 10})
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('Connection successful!')
except Exception as e:
    print(f'ERROR: Database connection failed: {e}')
    sys.exit(1)
"
        
        if [ $? -eq 0 ]; then
            echo "Database connection successful, running migrations..."
            alembic upgrade head
            if [ $? -eq 0 ]; then
                echo "Migrations completed successfully!"
                return 0
            else
                echo "Alembic migrations failed"
            fi
        fi
        
        echo "Attempt $attempt failed, waiting ${wait_time}s before retry..."
        sleep $wait_time
        attempt=$((attempt + 1))
        wait_time=$((wait_time * 2))  # Exponential backoff
    done
    
    echo "ERROR: All migration attempts failed"
    return 1
}

# Run migrations with retries (but don't exit on failure - let the server start)
echo "Running database migrations..."
if ! run_migrations; then
    echo "WARNING: Migrations failed, but starting server anyway"
    echo "The server will start but may have limited functionality"
fi

echo "=============================================="
echo "Starting uvicorn..."
echo "=============================================="

# Start uvicorn (exec replaces shell process)
# Using 2 workers instead of 4 to reduce memory and startup time
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
