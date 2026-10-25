"""RequestExecution SQLAlchemy ORM Model."""

from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base, utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.saved_request import SavedRequest


class RequestExecution(Base):
    """Stores the execution log and results of an outbound HTTP call."""

    __tablename__ = "request_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    # Ownership and origin
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    saved_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("saved_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Executed request snapshot
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    request_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    request_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response details
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    response_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Assertion outcomes and errors
    assertion_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="executions")
    saved_request: Mapped[Optional["SavedRequest"]] = relationship(
        "SavedRequest", back_populates="executions"
    )

    def __repr__(self) -> str:
        return f"<RequestExecution id={self.id} method={self.method} status={self.status_code}>"

