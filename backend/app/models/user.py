"""User SQLAlchemy ORM Model."""

from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, utc_now

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.saved_request import SavedRequest
    from app.models.request_execution import RequestExecution


class User(Base):
    """Represents a registered user in the system."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships - cascading deletes ensure orphaned records are cleaned up
    collections: Mapped[List["Collection"]] = relationship(
        "Collection", back_populates="user", cascade="all, delete-orphan"
    )
    saved_requests: Mapped[List["SavedRequest"]] = relationship(
        "SavedRequest", back_populates="user", cascade="all, delete-orphan"
    )
    executions: Mapped[List["RequestExecution"]] = relationship(
        "RequestExecution", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

