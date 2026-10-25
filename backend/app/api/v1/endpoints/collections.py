"""Collection API Endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.collection import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
    CollectionPagination,
)
from app.services.collection_service import collection_service

router = APIRouter()


@router.post(
    "/",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new collection",
)
def create_collection(
    collection_in: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionResponse:
    """Create a new collection owned by the current authenticated user."""
    return collection_service.create_collection(
        db=db, obj_in=collection_in, user=current_user
    )


@router.get(
    "/",
    response_model=CollectionPagination,
    status_code=status.HTTP_200_OK,
    summary="List user collections (paginated)",
)
def list_collections(
    page: int = Query(1, ge=1, description="Page number (starting at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1 to 100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionPagination:
    """Retrieve all collections owned by the current authenticated user with pagination."""
    items, total, total_pages = collection_service.list_user_collections(
        db=db, user=current_user, page=page, page_size=page_size
    )
    return CollectionPagination(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get collection by ID",
)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionResponse:
    """Retrieve a specific collection by ID if it belongs to the authenticated user."""
    return collection_service.get_user_collection(
        db=db, collection_id=collection_id, user=current_user
    )


@router.put(
    "/{collection_id}",
    response_model=CollectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a collection",
)
def update_collection(
    collection_id: int,
    collection_in: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionResponse:
    """Update name or description of a collection owned by the authenticated user."""
    return collection_service.update_collection(
        db=db, collection_id=collection_id, obj_in=collection_in, user=current_user
    )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a collection",
)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a collection and all associated saved requests."""
    collection_service.delete_collection(
        db=db, collection_id=collection_id, user=current_user
    )

