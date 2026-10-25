"""Automated tests for Response Assertions and Execution History."""

from unittest.mock import patch, AsyncMock
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.collection import Collection
from app.models.saved_request import SavedRequest
from app.models.request_execution import RequestExecution
from app.services.assertion_engine import assertion_engine, extract_json_path


# -----------------------------------------------------------------------------
# Unit Tests: JSON Path Extraction & Assertion Engine
# -----------------------------------------------------------------------------

def test_extract_json_path_nested_and_arrays():
    """Verify safe traversal of nested dictionaries and lists."""
    sample = {
        "user": {
            "name": "Alice",
            "addresses": [
                {"city": "New York", "zip": "10001"},
                {"city": "Boston", "zip": "02108"},
            ],
        },
        "tags": ["admin", "dev"],
    }

    found, val = extract_json_path(sample, "user.name")
    assert found is True
    assert val == "Alice"

    found, val = extract_json_path(sample, "user.addresses.1.city")
    assert found is True
    assert val == "Boston"

    found, val = extract_json_path(sample, "tags.0")
    assert found is True
    assert val == "admin"

    # Non-existent paths
    assert extract_json_path(sample, "user.missing")[0] is False
    assert extract_json_path(sample, "user.addresses.99.city")[0] is False
    assert extract_json_path(sample, "tags.invalid")[0] is False


def test_status_code_assertions():
    """Verify status code assertion passes on match and fails on mismatch."""
    # Match
    res_pass = assertion_engine.evaluate(
        assertions=[{"type": "status_code", "operator": "equals", "expected": 200}],
        status_code=200,
        response_time_ms=50.0,
        response_headers={},
        response_body="{}",
    )
    assert len(res_pass) == 1
    assert res_pass[0]["passed"] is True

    # Mismatch
    res_fail = assertion_engine.evaluate(
        assertions=[{"type": "status_code", "operator": "equals", "expected": 200}],
        status_code=404,
        response_time_ms=50.0,
        response_headers={},
        response_body="{}",
    )
    assert res_fail[0]["passed"] is False
    assert "Expected status 200, got 404" in res_fail[0]["message"]


def test_response_time_assertions():
    """Verify response time assertions."""
    # Under limit -> pass
    res_pass = assertion_engine.evaluate(
        assertions=[{"type": "response_time", "operator": "less_than", "expected": 200}],
        status_code=200,
        response_time_ms=120.5,
        response_headers={},
        response_body="{}",
    )
    assert res_pass[0]["passed"] is True

    # Over limit -> fail
    res_fail = assertion_engine.evaluate(
        assertions=[{"type": "response_time", "operator": "less_than", "expected": 100}],
        status_code=200,
        response_time_ms=250.0,
        response_headers={},
        response_body="{}",
    )
    assert res_fail[0]["passed"] is False


def test_json_field_assertions():
    """Verify json_field assertions for equals, contains, exists, and null."""
    body = '{"success": true, "data": {"token": "xyz123", "items": [10, 20]}, "error": null}'

    assertions = [
        {"type": "json_field", "path": "success", "operator": "equals", "expected": True},
        {"type": "json_field", "path": "data.token", "operator": "equals", "expected": "xyz123"},
        {"type": "json_field", "path": "data.items", "operator": "contains", "expected": 20},
        {"type": "json_field", "path": "data.items", "operator": "exists"},
        {"type": "json_field", "path": "error", "operator": "is_null"},
        {"type": "json_field", "path": "nonexistent", "operator": "exists"},
    ]

    results = assertion_engine.evaluate(
        assertions=assertions,
        status_code=200,
        response_time_ms=45.0,
        response_headers={},
        response_body=body,
    )

    assert results[0]["passed"] is True
    assert results[1]["passed"] is True
    assert results[2]["passed"] is True
    assert results[3]["passed"] is True
    assert results[4]["passed"] is True
    assert results[5]["passed"] is False  # nonexistent field should fail


def test_json_assertion_with_invalid_json_body():
    """Verify non-JSON response body fails assertion gracefully without throwing exception."""
    results = assertion_engine.evaluate(
        assertions=[{"type": "json_field", "path": "user.id", "expected": 1}],
        status_code=200,
        response_time_ms=10.0,
        response_headers={},
        response_body="<html><body>Internal Server Error</body></html>",
    )
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert "not valid json" in results[0]["message"].lower()


# -----------------------------------------------------------------------------
# End-to-End Tests: Execution History API & Assertion Integration
# -----------------------------------------------------------------------------

def test_execution_persists_history_and_masks_sensitive_headers(client: TestClient):
    """Verify that executing a request saves history, evaluates assertions, and redacts authorization."""
    fake_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        text='{"status": "ok", "user_id": 42}',
        request=httpx.Request("POST", "https://api.example.com/login"),
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = fake_response
        with patch("app.services.http_executor.validate_outbound_url", return_value="https://api.example.com/login"):
            payload = {
                "method": "POST",
                "url": "https://api.example.com/login",
                "headers": {
                    "Authorization": "Bearer sensitive_secret_token",
                    "Custom-Header": "VisibleValue",
                },
                "body": '{"username": "testuser"}',
                "assertions": [
                    {"type": "status_code", "operator": "equals", "expected": 200},
                    {"type": "json_field", "path": "user_id", "operator": "equals", "expected": 42},
                ],
            }

            res = client.post("/api/v1/requests/execute", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["execution_id"] is not None
            assert len(data["assertion_results"]) == 2
            assert all(r["passed"] for r in data["assertion_results"])

            # Verify history record in database
            exec_id = data["execution_id"]
            history_res = client.get(f"/api/v1/history/{exec_id}")
            assert history_res.status_code == 200
            hist = history_res.json()
            assert hist["url"] == "https://api.example.com/login"
            assert hist["status_code"] == 200
            # SENSITIVE HEADER MUST BE REDACTED
            assert hist["request_headers"]["Authorization"] == "[REDACTED]"
            assert hist["request_headers"]["Custom-Header"] == "VisibleValue"


def test_list_and_delete_execution_history(client: TestClient, db_session: Session, test_user: User):
    """Verify listing paginated execution history and deleting records."""
    # Create 3 history records
    for i in range(3):
        db_session.add(
            RequestExecution(
                user_id=test_user.id,
                method="GET",
                url=f"https://api.example.com/page/{i}",
                status_code=200,
                response_time_ms=100.0,
            )
        )
    db_session.commit()

    # List history
    list_res = client.get("/api/v1/history/?page=1&page_size=2")
    assert list_res.status_code == 200
    data = list_res.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 3

    # Delete one record
    item_id = data["items"][0]["id"]
    del_res = client.delete(f"/api/v1/history/{item_id}")
    assert del_res.status_code == 204

    # Verify deleted record is gone (404)
    get_res = client.get(f"/api/v1/history/{item_id}")
    assert get_res.status_code == 404


def test_user_isolation_on_execution_history(
    client: TestClient, db_session: Session, second_user: User
):
    """Verify User A cannot view or delete User B's execution history."""
    b_exec = RequestExecution(
        user_id=second_user.id,
        method="POST",
        url="https://api.example.com/secret",
        status_code=200,
        response_time_ms=88.0,
    )
    db_session.add(b_exec)
    db_session.commit()
    db_session.refresh(b_exec)

    # User A tries to GET User B's history record -> 404
    assert client.get(f"/api/v1/history/{b_exec.id}").status_code == 404

    # User A tries to DELETE User B's history record -> 404
    assert client.delete(f"/api/v1/history/{b_exec.id}").status_code == 404

