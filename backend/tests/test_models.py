"""Tests for database models, constraints, and relationships."""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.collection import Collection
from app.models.saved_request import SavedRequest
from app.models.request_execution import RequestExecution


def test_create_user(db_session: Session):
    """Verify user creation with email and password hash."""
    user = User(
        email="john.doe@example.com",
        hashed_password="securepasswordhash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "john.doe@example.com"
    assert user.is_active is True
    assert user.created_at is not None


def test_user_email_unique_constraint(db_session: Session, test_user: User):
    """Verify that creating two users with the same email raises IntegrityError."""
    duplicate_user = User(
        email=test_user.email,
        hashed_password="another_password_hash",
    )
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_collection_and_saved_request_cascade(db_session: Session, test_user: User):
    """Verify that deleting a collection cascades and deletes all child saved requests."""
    collection = Collection(
        name="Auth Service APIs",
        description="Collection of authentication tests",
        user_id=test_user.id,
    )
    db_session.add(collection)
    db_session.commit()
    db_session.refresh(collection)

    req = SavedRequest(
        name="Login Request",
        method="POST",
        url="https://api.example.com/login",
        headers={"Content-Type": "application/json"},
        params={},
        body='{"username": "test"}',
        collection_id=collection.id,
        user_id=test_user.id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    req_id = req.id
    assert db_session.query(SavedRequest).filter(SavedRequest.id == req_id).first() is not None

    # Delete parent collection
    db_session.delete(collection)
    db_session.commit()

    # Child saved request must be deleted automatically by cascade
    assert db_session.query(SavedRequest).filter(SavedRequest.id == req_id).first() is None


def test_request_execution_creation(db_session: Session, test_user: User):
    """Verify logging a request execution record."""
    execution = RequestExecution(
        user_id=test_user.id,
        method="GET",
        url="https://httpbin.org/get",
        status_code=200,
        response_time_ms=124.5,
        response_headers={"content-type": "application/json"},
        response_body='{"origin": "1.2.3.4"}',
    )
    db_session.add(execution)
    db_session.commit()
    db_session.refresh(execution)

    assert execution.id is not None
    assert execution.status_code == 200
    assert execution.response_time_ms == 124.5
    assert execution.created_at is not None

