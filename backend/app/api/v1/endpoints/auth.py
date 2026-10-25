"""Authentication API Endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user with an email and password.

    Passwords are never stored in plaintext and are securely hashed with bcrypt.
    """
    return auth_service.register_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login (JSON)",
)
def login(
    login_in: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate with email and password via JSON payload, returning a JWT access token."""
    user = auth_service.authenticate_user(
        db=db, email=login_in.email, password=login_in.password
    )
    return auth_service.create_token_for_user(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile information of the currently authenticated user."""
    return current_user
