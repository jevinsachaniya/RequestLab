"""SavedRequest SQLAlchemy ORM Model."""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.collection import Collection
    from app.models.request_execution import RequestExecution


class SavedRequest(Base):
    """Represents a saved HTTP request (URL, method, headers, params, body, assertions)."""

    __tablename__ = "saved_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="GET")
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Key-value maps stored as structured JSON
    headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assertions: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, default=list, nullable=True)

    # Foreign Keys
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="saved_requests")
    user: Mapped["User"] = relationship("User", back_populates="saved_requests")
    executions: Mapped[List["RequestExecution"]] = relationship(
        "RequestExecution", back_populates="saved_request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SavedRequest id={self.id} name={self.name} method={self.method}>"

