"""
Create all database tables.
"""
import sys
sys.path.append('.')

from app.core.database import engine, Base
from app.models.user import User
from app.models.property import Property, DVFRecord
from app.models.document import Document
from app.models.analysis import Analysis

# Import all models to ensure they're registered with Base
print("Creating all database tables...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("✓ All tables created successfully!")
print("\nCreated tables:")
for table in Base.metadata.sorted_tables:
    print(f"  - {table.name}")
