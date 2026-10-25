"""User Database Repository."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    """Repository handling database operations for users."""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch a user by primary key ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch a user by unique email address (case-insensitive)."""
        return db.query(User).filter(User.email == email.strip().lower()).first()

    @staticmethod
    def create(db: Session, email: str, hashed_password: str) -> User:
        """Create and persist a new user record."""
        user = User(
            email=email.strip().lower(),
            hashed_password=hashed_password,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


user_repository = UserRepository()

