"""add uuid columns to entities

Revision ID: d5e6f7g8h9i0
Revises: 25ffc9523881
Create Date: 2026-01-31

This migration adds UUID columns to users, properties, documents, and photos tables
for better entity identification and API design.
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7g8h9i0'
down_revision: Union[str, None] = '25ffc9523881'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add uuid column to users table
    op.add_column('users', sa.Column('uuid', sa.String(36), nullable=True))
    op.create_index('ix_users_uuid', 'users', ['uuid'], unique=True)
    
    # Add uuid column to properties table
    op.add_column('properties', sa.Column('uuid', sa.String(36), nullable=True))
    op.create_index('ix_properties_uuid', 'properties', ['uuid'], unique=True)
    
    # Add uuid column to documents table
    op.add_column('documents', sa.Column('uuid', sa.String(36), nullable=True))
    op.create_index('ix_documents_uuid', 'documents', ['uuid'], unique=True)
    
    # Add uuid column to photos table
    op.add_column('photos', sa.Column('uuid', sa.String(36), nullable=True))
    op.create_index('ix_photos_uuid', 'photos', ['uuid'], unique=True)
    
    # Generate UUIDs for existing rows
    # Use raw SQL for better performance on large datasets
    connection = op.get_bind()
    
    # Update users with UUIDs
    users = connection.execute(sa.text("SELECT id FROM users WHERE uuid IS NULL")).fetchall()
    for (user_id,) in users:
        connection.execute(
            sa.text("UPDATE users SET uuid = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": user_id}
        )
    
    # Update properties with UUIDs
    properties = connection.execute(sa.text("SELECT id FROM properties WHERE uuid IS NULL")).fetchall()
    for (prop_id,) in properties:
        connection.execute(
            sa.text("UPDATE properties SET uuid = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": prop_id}
        )
    
    # Update documents with UUIDs
    documents = connection.execute(sa.text("SELECT id FROM documents WHERE uuid IS NULL")).fetchall()
    for (doc_id,) in documents:
        connection.execute(
            sa.text("UPDATE documents SET uuid = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": doc_id}
        )
    
    # Update photos with UUIDs
    photos = connection.execute(sa.text("SELECT id FROM photos WHERE uuid IS NULL")).fetchall()
    for (photo_id,) in photos:
        connection.execute(
            sa.text("UPDATE photos SET uuid = :uuid WHERE id = :id"),
            {"uuid": str(uuid.uuid4()), "id": photo_id}
        )


def downgrade() -> None:
    # Drop uuid columns and indexes
    op.drop_index('ix_photos_uuid', table_name='photos')
    op.drop_column('photos', 'uuid')
    
    op.drop_index('ix_documents_uuid', table_name='documents')
    op.drop_column('documents', 'uuid')
    
    op.drop_index('ix_properties_uuid', table_name='properties')
    op.drop_column('properties', 'uuid')
    
    op.drop_index('ix_users_uuid', table_name='users')
    op.drop_column('users', 'uuid')
