"""Execution History Business Service."""

from typing import Tuple, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.request_execution import RequestExecution
from app.models.user import User
from app.repositories.execution_repository import execution_repository


class HistoryService:
    """Service providing business logic for execution history."""

    @staticmethod
    def get_execution(db: Session, execution_id: int, user: User) -> RequestExecution:
        """Fetch a specific execution log, raising HTTP 404 if not found or unauthorized."""
        execution = execution_repository.get_by_id_and_user(
            db, execution_id=execution_id, user_id=user.id
        )
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution record with ID {execution_id} not found.",
            )
        return execution

    @staticmethod
    def list_history(
        db: Session,
        user: User,
        saved_request_id: Optional[int] = None,
        status_code: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[RequestExecution], int, int]:
        """List paginated execution records owned by the current user."""
        return execution_repository.get_multi_by_user(
            db=db,
            user_id=user.id,
            saved_request_id=saved_request_id,
            status_code=status_code,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def delete_execution(db: Session, execution_id: int, user: User) -> None:
        """Delete an execution log owned by the user."""
        execution = HistoryService.get_execution(db, execution_id=execution_id, user=user)
        execution_repository.delete(db, db_obj=execution)


history_service = HistoryService()

