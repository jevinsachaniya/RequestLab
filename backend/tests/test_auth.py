"""Automated tests for Authentication, JWT tokens, and Ownership enforcement."""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.models.collection import Collection
from app.main import app
from app.api.deps import get_db


@pytest.fixture
def unauthenticated_client(db_session: Session) -> TestClient:
    """A TestClient that does NOT mock get_current_user, testing real JWT validation."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_user_success(unauthenticated_client: TestClient):
    """Verify registration creates a user and returns HTTP 201 without password hash."""
    payload = {
        "email": "newuser@example.com",
        "password": "strongPassword123!",
    }
    response = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data  # Never expose password hash


def test_register_user_duplicate_email(unauthenticated_client: TestClient):
    """Verify duplicate email registration returns HTTP 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "strongPassword123!",
    }
    res1 = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_register_user_invalid_inputs(unauthenticated_client: TestClient):
    """Verify validation errors for short password (< 8 chars) or malformed email."""
    # Short password
    res1 = unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )
    assert res1.status_code == 422

    # Malformed email
    res2 = unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "validPassword123"},
    )
    assert res2.status_code == 422


def test_login_success(unauthenticated_client: TestClient):
    """Verify successful login returns valid JWT access token."""
    # Register user first
    unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "loginuser@example.com", "password": "correctPassword123"},
    )

    # Login
    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "correctPassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_invalid_password(unauthenticated_client: TestClient):
    """Verify incorrect password returns HTTP 401 Unauthorized."""
    unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "badpass@example.com", "password": "correctPassword123"},
    )

    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"email": "badpass@example.com", "password": "wrongPassword123"},
    )
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_login_nonexistent_user(unauthenticated_client: TestClient):
    """Verify logging in with non-existent email returns HTTP 401."""
    response = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "password12345"},
    )
    assert response.status_code == 401


def test_get_current_user_profile(unauthenticated_client: TestClient):
    """Verify /auth/me returns current user profile when given valid Bearer token."""
    # Register and login
    unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "profile@example.com", "password": "secretPassword123"},
    )
    token_res = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"email": "profile@example.com", "password": "secretPassword123"},
    )
    token = token_res.json()["access_token"]

    # Call /auth/me with Bearer token header
    response = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "profile@example.com"


def test_unauthorized_access_without_token(unauthenticated_client: TestClient):
    """Verify protected endpoints return HTTP 401 when no token is provided."""
    res1 = unauthenticated_client.get("/api/v1/auth/me")
    assert res1.status_code == 401

    res2 = unauthenticated_client.get("/api/v1/collections/")
    assert res2.status_code == 401


def test_invalid_and_expired_tokens(
    unauthenticated_client: TestClient, db_session: Session
):
    """Verify rejection of invalid signature and expired tokens."""
    # 1. Invalid / malformed token
    res1 = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert res1.status_code == 401

    # 2. Expired token
    # Create user in DB
    user = User(
        email="expired@example.com",
        hashed_password="mockpassword",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Generate token that expired 1 hour ago
    expired_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(hours=-1),
    )

    res2 = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res2.status_code == 401
    assert "expired" in res2.json()["detail"].lower()


def test_real_cross_user_isolation_with_tokens(
    unauthenticated_client: TestClient,
):
    """Verify that User A authenticated via JWT cannot access User B's resources."""
    # Register and login User A
    unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "userA@example.com", "password": "passwordUserA123"},
    )
    res_a = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"email": "userA@example.com", "password": "passwordUserA123"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register and login User B
    unauthenticated_client.post(
        "/api/v1/auth/register",
        json={"email": "userB@example.com", "password": "passwordUserB123"},
    )
    res_b = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"email": "userB@example.com", "password": "passwordUserB123"},
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B creates a secret collection
    b_col = unauthenticated_client.post(
        "/api/v1/collections/",
        json={"name": "User B Secret Collection"},
        headers=headers_b,
    ).json()
    b_col_id = b_col["id"]

    # User A tries to read User B's collection -> must return 404 (Not Found, hiding existence)
    res_get = unauthenticated_client.get(
        f"/api/v1/collections/{b_col_id}", headers=headers_a
    )
    assert res_get.status_code == 404

    # User A tries to edit User B's collection -> must return 404
    res_put = unauthenticated_client.put(
        f"/api/v1/collections/{b_col_id}",
        json={"name": "User A tampered"},
        headers=headers_a,
    )
    assert res_put.status_code == 404

    # User A tries to delete User B's collection -> must return 404
    res_del = unauthenticated_client.delete(
        f"/api/v1/collections/{b_col_id}", headers=headers_a
    )
    assert res_del.status_code == 404

    # Verify User B's collection is still intact
    res_b_check = unauthenticated_client.get(
        f"/api/v1/collections/{b_col_id}", headers=headers_b
    )
    assert res_b_check.status_code == 200
    assert res_b_check.json()["name"] == "User B Secret Collection"

