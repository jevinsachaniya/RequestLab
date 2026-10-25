"""Saved Request and Request Execution API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.saved_request import (
    SavedRequestCreate,
    SavedRequestUpdate,
    SavedRequestResponse,
    SavedRequestPagination,
)
from app.schemas.execution import RequestExecute, ExecutionResponse
from app.services.saved_request_service import saved_request_service
from app.services.http_executor import http_executor

router = APIRouter()


# -----------------------------------------------------------------------------
# Saved Request CRUD Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/collections/{collection_id}/requests",
    response_model=SavedRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a saved request inside a collection",
)
def create_saved_request(
    collection_id: int,
    request_in: SavedRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedRequestResponse:
    """Save an API request inside a user-owned collection."""
    return saved_request_service.create_saved_request(
        db=db,
        collection_id=collection_id,
        obj_in=request_in,
        user=current_user,
    )


@router.get(
    "/collections/{collection_id}/requests",
    response_model=SavedRequestPagination,
    status_code=status.HTTP_200_OK,
    summary="List saved requests in a collection (paginated)",
)
def list_requests_in_collection(
    collection_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedRequestPagination:
    """Retrieve all saved requests inside a user-owned collection with pagination."""
    items, total, total_pages = saved_request_service.list_requests_in_collection(
        db=db,
        collection_id=collection_id,
        user=current_user,
        page=page,
        page_size=page_size,
    )
    return SavedRequestPagination(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/requests/{request_id}",
    response_model=SavedRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved request by ID",
)
def get_saved_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedRequestResponse:
    """Retrieve a single saved request owned by the authenticated user."""
    return saved_request_service.get_user_request(
        db=db, request_id=request_id, user=current_user
    )


@router.put(
    "/requests/{request_id}",
    response_model=SavedRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a saved request",
)
def update_saved_request(
    request_id: int,
    request_in: SavedRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedRequestResponse:
    """Update details of a saved request owned by the authenticated user."""
    return saved_request_service.update_saved_request(
        db=db, request_id=request_id, obj_in=request_in, user=current_user
    )


@router.delete(
    "/requests/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved request",
)
def delete_saved_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a saved request owned by the authenticated user."""
    saved_request_service.delete_saved_request(
        db=db, request_id=request_id, user=current_user
    )


# -----------------------------------------------------------------------------
# HTTP Request Execution Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/requests/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a temporary / ad-hoc HTTP request (Guests allowed)",
)
async def execute_temporary_request(
    exec_in: RequestExecute,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> ExecutionResponse:
    """Execute an ad-hoc HTTP request. Guests can test freely; authenticated users get history persisted."""
    result = await http_executor.execute_request(
        method=exec_in.method,
        url=exec_in.url,
        headers=exec_in.headers,
        params=exec_in.params,
        body=exec_in.body,
        follow_redirects=exec_in.follow_redirects,
    )

    # Evaluate automated assertions if requested
    assertion_results = []
    if exec_in.assertions:
        from app.services.assertion_engine import assertion_engine
        assertion_results = assertion_engine.evaluate(
            assertions=exec_in.assertions,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
            response_headers=result.response_headers,
            response_body=result.response_body,
        )

    # Persist execution history ONLY for authenticated users
    history_id = None
    if current_user:
        from app.repositories.execution_repository import execution_repository
        history_record = execution_repository.create(
            db=db,
            user_id=current_user.id,
            saved_request_id=None,
            method=exec_in.method,
            url=exec_in.url,
            request_headers=exec_in.headers,
            request_body=exec_in.body,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
            response_headers=result.response_headers,
            response_body=result.response_body,
            assertion_results=assertion_results,
            error_message=result.error_message,
        )
        history_id = history_record.id

    return ExecutionResponse(
        execution_id=history_id,
        status_code=result.status_code,
        response_time_ms=result.response_time_ms,
        response_headers=result.response_headers,
        response_body=result.response_body,
        assertion_results=assertion_results,
        error_message=result.error_message,
    )


@router.post(
    "/requests/{request_id}/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute an existing saved request",
)
async def execute_saved_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutionResponse:
    """Execute a saved request by ID, evaluate stored assertions, and save history."""
    saved_req = saved_request_service.get_user_request(
        db=db, request_id=request_id, user=current_user
    )

    result = await http_executor.execute_request(
        method=saved_req.method,
        url=saved_req.url,
        headers=saved_req.headers,
        params=saved_req.params,
        body=saved_req.body,
        follow_redirects=False,
    )

    # Evaluate automated assertions stored with the saved request
    assertion_results = []
    if saved_req.assertions:
        from app.services.assertion_engine import assertion_engine
        assertion_results = assertion_engine.evaluate(
            assertions=saved_req.assertions,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
            response_headers=result.response_headers,
            response_body=result.response_body,
        )

    # Persist execution history linked to this saved request
    from app.repositories.execution_repository import execution_repository
    history_record = execution_repository.create(
        db=db,
        user_id=current_user.id,
        saved_request_id=saved_req.id,
        method=saved_req.method,
        url=saved_req.url,
        request_headers=saved_req.headers,
        request_body=saved_req.body,
        status_code=result.status_code,
        response_time_ms=result.response_time_ms,
        response_headers=result.response_headers,
        response_body=result.response_body,
        assertion_results=assertion_results,
        error_message=result.error_message,
    )

    return ExecutionResponse(
        execution_id=history_record.id,
        status_code=result.status_code,
        response_time_ms=result.response_time_ms,
        response_headers=result.response_headers,
        response_body=result.response_body,
        assertion_results=assertion_results,
        error_message=result.error_message,
    )

