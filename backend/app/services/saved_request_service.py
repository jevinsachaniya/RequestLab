"""SavedRequest Business Service."""

from typing import Tuple, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.saved_request import SavedRequest
from app.models.user import User
from app.services.collection_service import collection_service
from app.repositories.saved_request_repository import saved_request_repository
from app.schemas.saved_request import SavedRequestCreate, SavedRequestUpdate


class SavedRequestService:
    """Service providing business logic for saved API requests."""

    @staticmethod
    def get_user_request(db: Session, request_id: int, user: User) -> SavedRequest:
        """Fetch a saved request or raise HTTP 404 if not found."""
        saved_req = saved_request_repository.get_by_id_and_user(
            db, request_id=request_id, user_id=user.id
        )
        if not saved_req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved request with ID {request_id} not found.",
            )
        return saved_req

    @staticmethod
    def create_saved_request(
        db: Session,
        collection_id: int,
        obj_in: SavedRequestCreate,
        user: User,
    ) -> SavedRequest:
        """Create a new saved request inside a user-owned collection."""
        # Ensure parent collection belongs to current user
        collection_service.get_user_collection(db, collection_id=collection_id, user=user)

        obj_in.name = obj_in.name.strip()
        obj_in.url = obj_in.url.strip()
        obj_in.method = obj_in.method.strip().upper()

        return saved_request_repository.create(
            db=db,
            obj_in=obj_in,
            collection_id=collection_id,
            user_id=user.id,
        )

    @staticmethod
    def list_requests_in_collection(
        db: Session,
        collection_id: int,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SavedRequest], int, int]:
        """List paginated saved requests inside a user-owned collection."""
        # Ensure collection exists and belongs to current user
        collection_service.get_user_collection(db, collection_id=collection_id, user=user)

        return saved_request_repository.get_multi_by_collection(
            db=db,
            collection_id=collection_id,
            user_id=user.id,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def update_saved_request(
        db: Session,
        request_id: int,
        obj_in: SavedRequestUpdate,
        user: User,
    ) -> SavedRequest:
        """Update an existing saved request owned by the user."""
        saved_req = SavedRequestService.get_user_request(db, request_id=request_id, user=user)

        if obj_in.name is not None:
            obj_in.name = obj_in.name.strip()
        if obj_in.url is not None:
            obj_in.url = obj_in.url.strip()
        if obj_in.method is not None:
            obj_in.method = obj_in.method.strip().upper()

        return saved_request_repository.update(db=db, db_obj=saved_req, obj_in=obj_in)

    @staticmethod
    def delete_saved_request(db: Session, request_id: int, user: User) -> None:
        """Delete an existing saved request owned by the user."""
        saved_req = SavedRequestService.get_user_request(db, request_id=request_id, user=user)
        saved_request_repository.delete(db=db, db_obj=saved_req)


saved_request_service = SavedRequestService()

