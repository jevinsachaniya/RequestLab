"""Collection Database Repository.

Encapsulates all database query logic for collections, strictly enforcing user ownership.
"""

import math
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.collection import Collection
from app.schemas.collection import CollectionCreate, CollectionUpdate


class CollectionRepository:
    """Repository handling database operations for collections."""

    @staticmethod
    def get_by_id_and_user(
        db: Session, collection_id: int, user_id: int
    ) -> Optional[Collection]:
        """Fetch a single collection by its ID, ensuring it belongs to the given user."""
        return (
            db.query(Collection)
            .filter(Collection.id == collection_id, Collection.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_multi_by_user(
        db: Session, user_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Collection], int, int]:
        """Fetch a paginated list of collections belonging to the given user.

        Returns: (items, total_count, total_pages)
        """
        # Count total items for this user
        total = (
            db.query(func.count(Collection.id))
            .filter(Collection.user_id == user_id)
            .scalar()
            or 0
        )

        offset = (page - 1) * page_size
        items = (
            db.query(Collection)
            .filter(Collection.user_id == user_id)
            .order_by(Collection.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return items, total, total_pages

    @staticmethod
    def create(db: Session, obj_in: CollectionCreate, user_id: int) -> Collection:
        """Create and persist a new collection associated with the user."""
        db_obj = Collection(
            name=obj_in.name,
            description=obj_in.description,
            user_id=user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(
        db: Session, db_obj: Collection, obj_in: CollectionUpdate
    ) -> Collection:
        """Update an existing collection."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Collection) -> None:
        """Delete a collection from the database."""
        db.delete(db_obj)
        db.commit()


collection_repository = CollectionRepository()

