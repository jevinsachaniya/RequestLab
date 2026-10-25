"""Automated tests for Collection CRUD endpoints and user isolation."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.collection import Collection
from app.main import app
from app.api.deps import get_db, get_current_user


def test_create_collection_success(client: TestClient):
    """Verify creating a new collection returns status 201 and valid response schema."""
    payload = {
        "name": "Payment Gateway APIs",
        "description": "Endpoints for Stripe and PayPal integrations",
    }
    response = client.post("/api/v1/collections/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Payment Gateway APIs"
    assert data["description"] == "Endpoints for Stripe and PayPal integrations"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_collection_validation_failure(client: TestClient):
    """Verify that an empty or missing name returns HTTP 422 Unprocessable Entity."""
    response = client.post("/api/v1/collections/", json={"name": ""})
    assert response.status_code == 422

    response = client.post("/api/v1/collections/", json={})
    assert response.status_code == 422


def test_get_collection_by_id(client: TestClient):
    """Verify fetching an existing collection by ID."""
    # Create first
    created = client.post(
        "/api/v1/collections/",
        json={"name": "User Management APIs"},
    ).json()

    collection_id = created["id"]
    response = client.get(f"/api/v1/collections/{collection_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == collection_id
    assert data["name"] == "User Management APIs"


def test_get_nonexistent_collection_returns_404(client: TestClient):
    """Verify requesting a non-existent collection returns HTTP 404."""
    response = client.get("/api/v1/collections/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_collections_pagination(client: TestClient):
    """Verify pagination returns the correct page slice, total count, and total pages."""
    # Create 5 collections
    for i in range(5):
        client.post("/api/v1/collections/", json={"name": f"Collection {i}"})

    # Request page 1 with page_size 2
    response = client.get("/api/v1/collections/?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 5
    assert data["total_pages"] >= 3


def test_pagination_invalid_parameters(client: TestClient):
    """Verify invalid page (< 1) or excessive page_size (> 100) returns HTTP 422."""
    # Page must be >= 1
    res1 = client.get("/api/v1/collections/?page=0")
    assert res1.status_code == 422

    # Page size must be <= 100
    res2 = client.get("/api/v1/collections/?page_size=101")
    assert res2.status_code == 422


def test_update_collection(client: TestClient):
    """Verify updating collection name and description."""
    created = client.post(
        "/api/v1/collections/",
        json={"name": "Initial Name", "description": "Initial Desc"},
    ).json()

    col_id = created["id"]
    update_payload = {"name": "Updated Name", "description": "Updated Desc"}
    response = client.put(f"/api/v1/collections/{col_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated Desc"


def test_delete_collection(client: TestClient):
    """Verify deleting a collection returns HTTP 204 and removes it."""
    created = client.post(
        "/api/v1/collections/",
        json={"name": "To be deleted"},
    ).json()
    col_id = created["id"]

    delete_res = client.delete(f"/api/v1/collections/{col_id}")
    assert delete_res.status_code == 204

    # Verify subsequent fetch returns 404
    get_res = client.get(f"/api/v1/collections/{col_id}")
    assert get_res.status_code == 404


def test_user_isolation_for_collections(
    db_session: Session, test_user: User, second_user: User
):
    """Verify that User A cannot see, update, or delete User B's collections."""
    # Create collection belonging to second_user directly in DB
    b_collection = Collection(
        name="Private to User B",
        description="Confidential",
        user_id=second_user.id,
    )
    db_session.add(b_collection)
    db_session.commit()
    db_session.refresh(b_collection)

    # Client is authenticated as test_user (User A)
    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        # User A tries to GET User B's collection -> Must return 404 Not Found
        get_res = test_client.get(f"/api/v1/collections/{b_collection.id}")
        assert get_res.status_code == 404

        # User A tries to UPDATE User B's collection -> Must return 404 Not Found
        put_res = test_client.put(
            f"/api/v1/collections/{b_collection.id}",
            json={"name": "Hacked Collection"},
        )
        assert put_res.status_code == 404

        # User A tries to DELETE User B's collection -> Must return 404 Not Found
        del_res = test_client.delete(f"/api/v1/collections/{b_collection.id}")
        assert del_res.status_code == 404

        # User A lists collections -> Must not include User B's collection
        list_res = test_client.get("/api/v1/collections/")
        assert list_res.status_code == 200
        items = list_res.json()["items"]
        assert all(item["id"] != b_collection.id for item in items)

    app.dependency_overrides.clear()

