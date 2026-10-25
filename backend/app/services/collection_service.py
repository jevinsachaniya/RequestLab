"""Collection Business Service.

Coordinates validation, business rules, and repository operations.
"""

from typing import Tuple, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.collection import Collection
from app.models.user import User
from app.repositories.collection_repository import collection_repository
from app.schemas.collection import CollectionCreate, CollectionUpdate


class CollectionService:
    """Service providing collection business logic."""

    @staticmethod
    def get_user_collection(db: Session, collection_id: int, user: User) -> Collection:
        """Retrieve a specific collection or raise HTTP 404 if not found."""
        collection = collection_repository.get_by_id_and_user(
            db, collection_id=collection_id, user_id=user.id
        )
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection with ID {collection_id} not found.",
            )
        return collection

    @staticmethod
    def list_user_collections(
        db: Session, user: User, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Collection], int, int]:
        """List paginated collections for the given user."""
        return collection_repository.get_multi_by_user(
            db, user_id=user.id, page=page, page_size=page_size
        )

    @staticmethod
    def create_collection(
        db: Session, obj_in: CollectionCreate, user: User
    ) -> Collection:
        """Create a new collection for the given user."""
        # Sanitize whitespace
        obj_in.name = obj_in.name.strip()
        if obj_in.description:
            obj_in.description = obj_in.description.strip()
        return collection_repository.create(db, obj_in=obj_in, user_id=user.id)

    @staticmethod
    def update_collection(
        db: Session, collection_id: int, obj_in: CollectionUpdate, user: User
    ) -> Collection:
        """Update an existing collection owned by the user."""
        collection = CollectionService.get_user_collection(db, collection_id, user)
        if obj_in.name is not None:
            obj_in.name = obj_in.name.strip()
        if obj_in.description is not None:
            obj_in.description = obj_in.description.strip()
        return collection_repository.update(db, db_obj=collection, obj_in=obj_in)

    @staticmethod
    def delete_collection(db: Session, collection_id: int, user: User) -> None:
        """Delete an existing collection owned by the user."""
        collection = CollectionService.get_user_collection(db, collection_id, user)
        collection_repository.delete(db, db_obj=collection)


collection_service = CollectionService()

