"""Execution History API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.execution import (
    ExecutionHistoryResponse,
    ExecutionHistoryPagination,
)
from app.services.history_service import history_service

router = APIRouter()


@router.get(
    "/",
    response_model=ExecutionHistoryPagination,
    status_code=status.HTTP_200_OK,
    summary="List request execution history (paginated)",
)
def list_execution_history(
    saved_request_id: Optional[int] = Query(None, description="Filter by saved request ID"),
    status_code: Optional[int] = Query(None, description="Filter by HTTP status code"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutionHistoryPagination:
    """Retrieve execution history logs for the current user with pagination and optional filters."""
    items, total, total_pages = history_service.list_history(
        db=db,
        user=current_user,
        saved_request_id=saved_request_id,
        status_code=status_code,
        page=page,
        page_size=page_size,
    )
    return ExecutionHistoryPagination(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{execution_id}",
    response_model=ExecutionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get execution history details by ID",
)
def get_execution_record(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutionHistoryResponse:
    """Retrieve full details of an execution log, verifying user ownership."""
    return history_service.get_execution(
        db=db, execution_id=execution_id, user=current_user
    )


@router.delete(
    "/{execution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an execution history record",
)
def delete_execution_record(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an execution log belonging to the authenticated user."""
    history_service.delete_execution(
        db=db, execution_id=execution_id, user=current_user
    )

