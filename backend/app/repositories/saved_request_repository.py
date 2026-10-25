"""SavedRequest Database Repository.

Encapsulates database operations for saved requests with user ownership isolation.
"""

import math
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.saved_request import SavedRequest
from app.schemas.saved_request import SavedRequestCreate, SavedRequestUpdate


class SavedRequestRepository:
    """Repository handling database operations for saved requests."""

    @staticmethod
    def get_by_id_and_user(
        db: Session, request_id: int, user_id: int
    ) -> Optional[SavedRequest]:
        """Fetch a saved request ensuring it belongs to the given user."""
        return (
            db.query(SavedRequest)
            .filter(SavedRequest.id == request_id, SavedRequest.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_multi_by_collection(
        db: Session, collection_id: int, user_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[SavedRequest], int, int]:
        """Fetch paginated saved requests for a collection owned by the user."""
        total = (
            db.query(func.count(SavedRequest.id))
            .filter(
                SavedRequest.collection_id == collection_id,
                SavedRequest.user_id == user_id,
            )
            .scalar()
            or 0
        )

        offset = (page - 1) * page_size
        items = (
            db.query(SavedRequest)
            .filter(
                SavedRequest.collection_id == collection_id,
                SavedRequest.user_id == user_id,
            )
            .order_by(SavedRequest.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return items, total, total_pages

    @staticmethod
    def create(
        db: Session,
        obj_in: SavedRequestCreate,
        collection_id: int,
        user_id: int,
    ) -> SavedRequest:
        """Create and persist a new saved request inside a collection."""
        db_obj = SavedRequest(
            name=obj_in.name,
            method=obj_in.method,
            url=obj_in.url,
            headers=obj_in.headers,
            params=obj_in.params,
            body=obj_in.body,
            assertions=obj_in.assertions,
            collection_id=collection_id,
            user_id=user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(
        db: Session,
        db_obj: SavedRequest,
        obj_in: SavedRequestUpdate,
    ) -> SavedRequest:
        """Update an existing saved request."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: SavedRequest) -> None:
        """Delete a saved request from the database."""
        db.delete(db_obj)
        db.commit()


saved_request_repository = SavedRequestRepository()

