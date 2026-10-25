"""Authentication Business Service."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, Token


class AuthService:
    """Service handling user registration, credential verification, and token creation."""

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user after verifying email uniqueness."""
        normalized_email = user_in.email.strip().lower()
        existing_user = user_repository.get_by_email(db, normalized_email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        hashed_password = get_password_hash(user_in.password)
        return user_repository.create(
            db=db,
            email=normalized_email,
            hashed_password=hashed_password,
        )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Verify user credentials and return the user if valid."""
        user = user_repository.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )
        return user

    @staticmethod
    def create_token_for_user(user: User) -> Token:
        """Create a signed JWT access token for an authenticated user."""
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token, token_type="bearer")


auth_service = AuthService()

