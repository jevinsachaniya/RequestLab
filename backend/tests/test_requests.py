"""Automated tests for Saved Requests CRUD and secure HTTP Execution Engine."""

from unittest.mock import patch, AsyncMock
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.collection import Collection
from app.models.saved_request import SavedRequest
from app.main import app
from app.api.deps import get_db, get_current_user


# -----------------------------------------------------------------------------
# Saved Request CRUD Tests
# -----------------------------------------------------------------------------

def test_create_saved_request_success(client: TestClient, db_session: Session, test_user: User):
    """Verify creating a saved request inside a user-owned collection."""
    # Create collection
    col = Collection(name="E-commerce APIs", user_id=test_user.id)
    db_session.add(col)
    db_session.commit()
    db_session.refresh(col)

    payload = {
        "name": "Get Product Details",
        "method": "GET",
        "url": "https://api.example.com/products/123",
        "headers": {"Accept": "application/json"},
        "params": {"detail": "true"},
        "body": None,
        "assertions": [{"type": "status_code", "expected": 200}],
    }

    response = client.post(f"/api/v1/collections/{col.id}/requests", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Get Product Details"
    assert data["method"] == "GET"
    assert data["url"] == "https://api.example.com/products/123"
    assert data["collection_id"] == col.id
    assert data["user_id"] == test_user.id
    assert len(data["assertions"]) == 1


def test_create_saved_request_in_other_user_collection_fails(
    client: TestClient, db_session: Session, second_user: User
):
    """Verify that User A cannot save requests into User B's collection."""
    b_col = Collection(name="User B Private", user_id=second_user.id)
    db_session.add(b_col)
    db_session.commit()
    db_session.refresh(b_col)

    payload = {
        "name": "Tampering Attempt",
        "method": "POST",
        "url": "https://api.example.com/evil",
    }

    response = client.post(f"/api/v1/collections/{b_col.id}/requests", json=payload)
    assert response.status_code == 404


def test_get_saved_request_by_id(client: TestClient, db_session: Session, test_user: User):
    """Verify fetching a saved request by ID."""
    col = Collection(name="Order APIs", user_id=test_user.id)
    db_session.add(col)
    db_session.commit()
    db_session.refresh(col)

    req = SavedRequest(
        name="Get Order",
        method="GET",
        url="https://api.example.com/orders/1",
        collection_id=col.id,
        user_id=test_user.id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    response = client.get(f"/api/v1/requests/{req.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Order"


def test_list_saved_requests_pagination(client: TestClient, db_session: Session, test_user: User):
    """Verify listing paginated saved requests inside a collection."""
    col = Collection(name="Batch Collection", user_id=test_user.id)
    db_session.add(col)
    db_session.commit()
    db_session.refresh(col)

    for i in range(4):
        db_session.add(
            SavedRequest(
                name=f"Request {i}",
                method="GET",
                url=f"https://api.example.com/items/{i}",
                collection_id=col.id,
                user_id=test_user.id,
            )
        )
    db_session.commit()

    response = client.get(f"/api/v1/collections/{col.id}/requests?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 4
    assert data["total_pages"] == 2


def test_update_saved_request(client: TestClient, db_session: Session, test_user: User):
    """Verify updating a saved request."""
    col = Collection(name="Test Col", user_id=test_user.id)
    db_session.add(col)
    db_session.commit()
    db_session.refresh(col)

    req = SavedRequest(
        name="Old Request Name",
        method="GET",
        url="https://api.example.com/old",
        collection_id=col.id,
        user_id=test_user.id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    update_payload = {
        "name": "Updated Request Name",
        "method": "POST",
        "url": "https://api.example.com/new",
        "body": '{"updated": true}',
    }
    response = client.put(f"/api/v1/requests/{req.id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Request Name"
    assert data["method"] == "POST"
    assert data["url"] == "https://api.example.com/new"
    assert data["body"] == '{"updated": true}'


def test_delete_saved_request(client: TestClient, db_session: Session, test_user: User):
    """Verify deleting a saved request."""
    col = Collection(name="Delete Col", user_id=test_user.id)
    db_session.add(col)
    db_session.commit()
    db_session.refresh(col)

    req = SavedRequest(
        name="To Delete",
        method="DELETE",
        url="https://api.example.com/remove",
        collection_id=col.id,
        user_id=test_user.id,
    )
    db_session.add(req)
    db_session.commit()
    db_session.refresh(req)

    req_id = req.id
    delete_res = client.delete(f"/api/v1/requests/{req_id}")
    assert delete_res.status_code == 204

    # Fetching after deletion must return 404
    get_res = client.get(f"/api/v1/requests/{req_id}")
    assert get_res.status_code == 404


def test_cross_user_isolation_on_saved_requests(
    client: TestClient, db_session: Session, second_user: User
):
    """Verify that User A cannot read, update, or delete User B's saved request."""
    b_col = Collection(name="User B Col", user_id=second_user.id)
    db_session.add(b_col)
    db_session.commit()
    db_session.refresh(b_col)

    b_req = SavedRequest(
        name="User B Private Request",
        method="GET",
        url="https://api.example.com/confidential",
        collection_id=b_col.id,
        user_id=second_user.id,
    )
    db_session.add(b_req)
    db_session.commit()
    db_session.refresh(b_req)

    # User A tries to GET
    assert client.get(f"/api/v1/requests/{b_req.id}").status_code == 404
    # User A tries to PUT
    assert client.put(f"/api/v1/requests/{b_req.id}", json={"name": "tamper"}).status_code == 404
    # User A tries to DELETE
    assert client.delete(f"/api/v1/requests/{b_req.id}").status_code == 404


# -----------------------------------------------------------------------------
# HTTP Execution Engine Tests (Mocked Outbound Calls)
# -----------------------------------------------------------------------------

def test_execute_temporary_request_mocked_success(client: TestClient):
    """Verify executing an ad-hoc request returns status, headers, body, and timing."""
    fake_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json", "x-custom": "sentinel"},
        text='{"message": "success", "count": 42}',
        request=httpx.Request("GET", "https://api.example.com/data"),
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = fake_response
        with patch("app.services.http_executor.validate_outbound_url", return_value="https://api.example.com/data"):
            payload = {
                "method": "GET",
                "url": "https://api.example.com/data",
                "headers": {"Accept": "application/json"},
                "params": {"query": "test"},
            }
            response = client.post("/api/v1/requests/execute", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status_code"] == 200
            assert "application/json" in data["response_headers"]["content-type"]
            assert '{"message": "success", "count": 42}' in data["response_body"]
            assert data["response_time_ms"] is not None
            assert data["error_message"] is None


def test_execute_request_ssrf_blocked(client: TestClient):
    """Verify that targeting an internal or metadata IP returns a clear security error."""
    payload = {
        "method": "GET",
        "url": "http://169.254.169.254/latest/meta-data/",
    }
    response = client.post("/api/v1/requests/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] is None
    assert "security violation" in data["error_message"].lower()


def test_execute_request_timeout_handling(client: TestClient):
    """Verify that timeout exceptions are caught and reported cleanly."""
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = httpx.TimeoutException("Connection timed out")
        with patch("app.services.http_executor.validate_outbound_url", return_value="https://api.example.com/slow"):
            payload = {
                "method": "GET",
                "url": "https://api.example.com/slow",
            }
            response = client.post("/api/v1/requests/execute", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status_code"] is None
            assert "timed out" in data["error_message"].lower()


def test_execute_saved_request_by_id(client: TestClient, db_session: Session, test_user: User):
    """Verify executing a saved request loads parameters from DB and returns response."""
    col = Collection(name="Exec Collection", user_id=test_user.id)
    db_session.add(col)
    db_session.commit()
    db_session.refresh(col)

    saved_req = SavedRequest(
        name="Execute Saved",
        method="POST",
        url="https://api.example.com/items",
        headers={"Content-Type": "application/json"},
        params={},
        body='{"item": "book"}',
        collection_id=col.id,
        user_id=test_user.id,
    )
    db_session.add(saved_req)
    db_session.commit()
    db_session.refresh(saved_req)

    fake_response = httpx.Response(
        status_code=201,
        headers={"content-type": "application/json"},
        text='{"id": 99, "item": "book"}',
        request=httpx.Request("POST", "https://api.example.com/items"),
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = fake_response
        with patch("app.services.http_executor.validate_outbound_url", return_value="https://api.example.com/items"):
            response = client.post(f"/api/v1/requests/{saved_req.id}/execute")
            assert response.status_code == 200
            data = response.json()
            assert data["status_code"] == 201
            assert '{"id": 99, "item": "book"}' in data["response_body"]


def test_guest_can_execute_request_without_token_no_history_saved(db_session: Session):
    """Verify unauthenticated guests can execute requests freely without logging history."""
    fake_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        text='{"guest": true, "public": "access"}',
        request=httpx.Request("GET", "https://api.example.com/guest"),
    )

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as guest_client:
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = fake_response
            with patch("app.services.http_executor.validate_outbound_url", return_value="https://api.example.com/guest"):
                payload = {
                    "method": "GET",
                    "url": "https://api.example.com/guest",
                    "assertions": [{"type": "status_code", "operator": "equals", "expected": 200}],
                }
                # Call without any Authorization header
                response = guest_client.post("/api/v1/requests/execute", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert data["status_code"] == 200
                assert data["execution_id"] is None  # Guest history is NOT persisted
                assert len(data["assertion_results"]) == 1
                assert data["assertion_results"][0]["passed"] is True

    app.dependency_overrides.clear()


