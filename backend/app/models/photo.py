"""
Photo model for apartment redesign feature.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
import uuid
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Photo(Base):
    """Model for uploaded apartment photos."""

    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    # Original photo
    filename = Column(String, nullable=False)
    minio_key = Column(String, nullable=False)  # Path in MinIO
    minio_bucket = Column(String, default="photos")
    file_size = Column(Integer)
    mime_type = Column(String)

    # Metadata
    room_type = Column(String, nullable=True)  # living_room, bedroom, kitchen, etc.
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    redesigns = relationship("PhotoRedesign", back_populates="original_photo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Photo {self.id}: {self.filename}>"


class PhotoRedesign(Base):
    """Model for AI-generated apartment redesigns."""

    __tablename__ = "photo_redesigns"

    id = Column(Integer, primary_key=True, index=True)
    redesign_uuid = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)

    # Generated image
    minio_key = Column(String, nullable=False)
    minio_bucket = Column(String, default="photos")
    file_size = Column(Integer)

    # Generation parameters
    style_preset = Column(String, nullable=True)  # modern_norwegian, minimalist_scandinavian, etc.
    prompt = Column(Text, nullable=False)
    aspect_ratio = Column(String, default="16:9")
    model_used = Column(String, default="gemini-2.5-flash-image")

    # Conversation history for multi-turn
    conversation_history = Column(JSON, nullable=True)
    is_multi_turn = Column(Boolean, default=False)
    parent_redesign_id = Column(Integer, ForeignKey("photo_redesigns.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    generation_time_ms = Column(Integer, nullable=True)

    # User feedback
    is_favorite = Column(Boolean, default=False)
    user_rating = Column(Integer, nullable=True)  # 1-5 stars

    # Relationships
    original_photo = relationship("Photo", back_populates="redesigns")
    parent_redesign = relationship("PhotoRedesign", remote_side=[id], backref="iterations")

    def __repr__(self):
        return f"<PhotoRedesign {self.id}: {self.style_preset or 'custom'}>"
