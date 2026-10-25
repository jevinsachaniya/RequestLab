"""Collection SQLAlchemy ORM Model."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.saved_request import SavedRequest


class Collection(Base):
    """Represents a folder/group of saved API requests belonging to a user."""

    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign key establishing ownership by a specific user
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="collections")
    saved_requests: Mapped[List["SavedRequest"]] = relationship(
        "SavedRequest", back_populates="collection", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Collection id={self.id} name={self.name} user_id={self.user_id}>"

