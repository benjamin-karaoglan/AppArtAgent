"""Users API routes for authentication and user management."""

import html as html_module
import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.better_auth_security import (
    get_better_auth_session,
    validate_session_token,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.i18n import get_local, translate
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.models.document import Document
from app.models.photo import Photo, PhotoRedesign
from app.models.property import Property
from app.models.user import User
from app.services.email import send_email
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()


class UserRegister(BaseModel):
    """User registration schema."""

    email: EmailStr
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str
    user_id: int
    email: str


class UserResponse(BaseModel):
    """User response schema."""

    id: int
    email: str
    full_name: str
    is_active: bool
    documents_analyzed_count: int = 0

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """User statistics response schema."""

    documents_analyzed_count: int
    redesigns_generated_count: int
    total_properties: int


# DEPRECATED: These endpoints are kept for backward compatibility during migration
# New registrations and logins should use Better Auth via Next.js


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user (DEPRECATED).

    This endpoint is deprecated. Use Better Auth via Next.js /api/auth/sign-up instead.
    Kept for backward compatibility during migration.
    """
    locale = get_local(request)

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=translate("email_already_registered", locale),
        )

    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=access_token, token_type="bearer", user_id=user.id, email=user.email
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Login user and return access token (DEPRECATED).

    This endpoint is deprecated. Use Better Auth via Next.js /api/auth/sign-in instead.
    Kept for backward compatibility during migration.
    """
    locale = get_local(request)

    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translate("incorrect_credentials", locale),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=translate("inactive_user", locale)
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=access_token, token_type="bearer", user_id=user.id, email=user.email
    )


async def get_user_from_auth(request: Request, db: Session) -> Optional[User]:
    """
    Get user from either Better Auth session or legacy JWT token.

    Tries Better Auth first, then falls back to JWT for backward compatibility.
    """
    # Try Better Auth session first
    session_token = await get_better_auth_session(request)
    if session_token:
        session_data = await validate_session_token(session_token, db)
        if session_data:
            # Find user by ba_user_id
            user = db.query(User).filter(User.ba_user_id == session_data["ba_user_id"]).first()
            if user:
                return user
            # User might exist in Better Auth but not linked - try by email
            user = db.query(User).filter(User.email == session_data["email"]).first()
            if user:
                # Auto-link the user
                user.ba_user_id = session_data["ba_user_id"]
                db.commit()
                return user
            # Create new user record for Better Auth user
            user = User(
                email=session_data["email"],
                full_name=session_data.get("name") or "",
                hashed_password="",  # No password - using Better Auth
                is_active=True,
                ba_user_id=session_data["ba_user_id"],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    # Fall back to legacy JWT
    try:
        current_user = await get_current_user(request)
        user = db.query(User).filter(User.id == int(current_user)).first()
        return user
    except Exception:
        return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get current user information.

    Supports both Better Auth sessions (via cookies) and legacy JWT tokens.
    """
    locale = get_local(request)

    user = await get_user_from_auth(request, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translate("not_authenticated", locale),
        )

    return user


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Get current user statistics.

    Supports both Better Auth sessions (via cookies) and legacy JWT tokens.
    """
    locale = get_local(request)

    user = await get_user_from_auth(request, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translate("not_authenticated", locale),
        )

    # Count properties
    property_count = db.query(Property).filter(Property.user_id == user.id).count()

    return UserStatsResponse(
        documents_analyzed_count=user.documents_analyzed_count or 0,
        redesigns_generated_count=user.redesigns_generated_count or 0,
        total_properties=property_count,
    )


class ResetEmailRequest(BaseModel):
    """Password reset email request."""

    email: EmailStr
    name: str = ""
    url: str


@router.post("/send-reset-email", status_code=status.HTTP_204_NO_CONTENT)
async def send_reset_email(data: ResetEmailRequest):
    """Send a password reset email via Resend. Called by Better Auth's sendResetPassword hook."""
    safe_name = html_module.escape(data.name or "there")
    safe_url = html_module.escape(data.url)

    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb; font-size: 24px; margin: 0;">AppArt Agent</h1>
      </div>
      <h2 style="color: #111827; font-size: 20px;">Reset your password</h2>
      <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
        Hi {safe_name}, we received a request to reset your password. Click the button below to set a new one:
      </p>
      <div style="text-align: center; margin: 30px 0;">
        <a href="{safe_url}" style="background-color: #2563eb; color: white; padding: 12px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; display: inline-block;">
          Reset Password
        </a>
      </div>
      <p style="color: #6b7280; font-size: 14px; line-height: 1.5;">
        If you didn't request this, you can safely ignore this email. The link will expire in 1 hour.
      </p>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;" />
      <p style="color: #9ca3af; font-size: 12px; text-align: center;">
        AppArt Agent — AI-powered apartment analysis
      </p>
    </div>
    """

    send_email(
        to=data.email,
        subject="[AppArt Agent] Reset your password",
        html_body=html_body,
    )
    # Always return 204 regardless of email success (don't leak whether email exists)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete current user account and all associated data.

    Cascading deletion order:
    1. Delete storage files (photos, documents) — best-effort
    2. Delete all database records (SQLAlchemy cascade handles most)
    3. Delete Better Auth data (sessions, accounts, user)
    4. Delete legacy user record
    """
    user = await get_user_from_auth(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    storage = StorageService()

    # 1. Best-effort storage file cleanup
    # Delete photo redesign files
    photos = db.query(Photo).filter(Photo.user_id == user.id).all()
    for photo in photos:
        redesigns = db.query(PhotoRedesign).filter(PhotoRedesign.photo_id == photo.id).all()
        for redesign in redesigns:
            try:
                storage.delete_file(redesign.storage_key, redesign.storage_bucket)
            except Exception:
                logger.warning(f"Failed to delete redesign file: {redesign.storage_key}")
        # Delete original photo file
        try:
            storage.delete_file(photo.storage_key, photo.storage_bucket)
        except Exception:
            logger.warning(f"Failed to delete photo file: {photo.storage_key}")

    # Delete document files
    documents = db.query(Document).filter(Document.user_id == user.id).all()
    for doc in documents:
        if doc.storage_key and doc.storage_bucket:
            try:
                storage.delete_file(doc.storage_key, doc.storage_bucket)
            except Exception:
                logger.warning(f"Failed to delete document file: {doc.storage_key}")

    # 2. Delete Better Auth data if linked
    if user.ba_user_id:
        try:
            from sqlalchemy import text

            # Delete sessions
            db.execute(
                text("DELETE FROM ba_session WHERE user_id = :uid"),
                {"uid": user.ba_user_id},
            )
            # Delete accounts (credentials, OAuth)
            db.execute(
                text("DELETE FROM ba_account WHERE user_id = :uid"),
                {"uid": user.ba_user_id},
            )
            # Delete verifications by email
            db.execute(
                text("DELETE FROM ba_verification WHERE identifier = :email"),
                {"email": user.email},
            )
            # Delete ba_user (must unlink first to avoid FK constraint)
            db.execute(
                text("UPDATE users SET ba_user_id = NULL WHERE id = :id"),
                {"id": user.id},
            )
            db.flush()
            db.execute(
                text("DELETE FROM ba_user WHERE id = :uid"),
                {"uid": user.ba_user_id},
            )
        except Exception:
            logger.exception("Failed to clean up Better Auth data")

    # 3. Delete user record (SQLAlchemy cascades handle properties, documents)
    db.delete(user)
    db.commit()

    logger.info(f"Account deleted: user_id={user.id}, email={user.email}")
