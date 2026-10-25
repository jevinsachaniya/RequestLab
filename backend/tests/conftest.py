"""Pytest fixtures and configuration for isolated testing."""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.main import app
from app.models.user import User

# Use an in-memory SQLite database for testing, completely isolated from development DB
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Shared connection across in-memory threads
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all database tables before tests run, drop them after all tests complete."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a clean database session per test with automatic rollback/cleanup."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Fixture providing a standard test user."""
    user = User(
        email="tester@apisentinel.local",
        hashed_password="mock_hashed_password_123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session: Session) -> User:
    """Fixture providing a second user to verify user isolation."""
    user = User(
        email="second_user@apisentinel.local",
        hashed_password="mock_hashed_password_456",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(db_session: Session, test_user: User) -> Generator[TestClient, None, None]:
    """TestClient with overridden database and current_user dependencies."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_optional] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
