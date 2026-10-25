# API Sentinel — Sample API Workflow

This guide demonstrates a complete end-to-end workflow using the API Sentinel REST API via `curl` or HTTP clients.

---

## 1. Register a New Account

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "password": "SuperSecretPassword123"
  }'
```

**Response (`201 Created`):**
```json
{
  "email": "developer@example.com",
  "id": 1,
  "is_active": true,
  "created_at": "2026-10-25T10:00:00Z",
  "updated_at": "2026-10-25T10:00:00Z"
}
```

---

## 2. Authenticate & Obtain JWT Token

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "password": "SuperSecretPassword123"
  }'
```

**Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **Note:** Save the token and pass it in the `Authorization: Bearer <TOKEN>` header for all subsequent calls.

---

## 3. Create an API Collection

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/collections/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-Commerce Microservices",
    "description": "Integration and smoke tests for order and catalog services."
  }'
```

**Response (`201 Created`):**
```json
{
  "name": "E-Commerce Microservices",
  "description": "Integration and smoke tests for order and catalog services.",
  "id": 1,
  "user_id": 1,
  "created_at": "2026-10-25T10:05:00Z",
  "updated_at": "2026-10-25T10:05:00Z"
}
```

---

## 4. Save a Request with Automated Assertions

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/collections/1/requests \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fetch HTTPBin IP",
    "method": "GET",
    "url": "https://httpbin.org/get",
    "headers": {
      "Accept": "application/json"
    },
    "params": {
      "test_param": "api_sentinel"
    },
    "body": null,
    "assertions": [
      {
        "type": "status_code",
        "operator": "equals",
        "expected": 200
      },
      {
        "type": "response_time",
        "operator": "less_than",
        "expected": 2000
      },
      {
        "type": "json_field",
        "path": "args.test_param",
        "operator": "equals",
        "expected": "api_sentinel"
      }
    ]
  }'
```

**Response (`201 Created`):**
```json
{
  "name": "Fetch HTTPBin IP",
  "method": "GET",
  "url": "https://httpbin.org/get",
  "headers": {"Accept": "application/json"},
  "params": {"test_param": "api_sentinel"},
  "body": null,
  "assertions": [
    {"type": "status_code", "operator": "equals", "expected": 200},
    {"type": "response_time", "operator": "less_than", "expected": 2000},
    {"type": "json_field", "path": "args.test_param", "operator": "equals", "expected": "api_sentinel"}
  ],
  "id": 1,
  "collection_id": 1,
  "user_id": 1,
  "created_at": "2026-10-25T10:10:00Z",
  "updated_at": "2026-10-25T10:10:00Z"
}
```

---

## 5. Execute the Saved Request

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/requests/1/execute \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (`200 OK`):**
```json
{
  "execution_id": 1,
  "status_code": 200,
  "response_time_ms": 142.5,
  "response_headers": {
    "content-type": "application/json",
    "server": "gunicorn"
  },
  "response_body": "{\n  \"args\": {\n    \"test_param\": \"api_sentinel\"\n  },\n  \"origin\": \"...\",\n  \"url\": \"https://httpbin.org/get?test_param=api_sentinel\"\n}",
  "assertion_results": [
    {
      "rule": {"type": "status_code", "operator": "equals", "expected": 200},
      "passed": true,
      "actual": 200,
      "message": "Status code is 200."
    },
    {
      "rule": {"type": "response_time", "operator": "less_than", "expected": 2000},
      "passed": true,
      "actual": 142.5,
      "message": "Response time 142.5ms < threshold 2000.0ms."
    },
    {
      "rule": {"type": "json_field", "path": "args.test_param", "operator": "equals", "expected": "api_sentinel"},
      "passed": true,
      "actual": "api_sentinel",
      "message": "Field 'args.test_param': expected 'api_sentinel', got 'api_sentinel'."
    }
  ],
  "error_message": null
}
```

---

## 6. Inspect Execution History Logs

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/history/?page=1&page_size=10" \
  -H "Authorization: Bearer <TOKEN>"
```

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "saved_request_id": 1,
      "method": "GET",
      "url": "https://httpbin.org/get",
      "request_headers": {
        "Accept": "application/json"
      },
      "request_body": null,
      "status_code": 200,
      "response_time_ms": 142.5,
      "response_headers": {
        "content-type": "application/json"
      },
      "response_body": "{\n  \"args\": {\n    \"test_param\": \"api_sentinel\" ...",
      "assertion_results": [
        {"passed": true, "message": "Status code is 200."}
      ],
      "error_message": null,
      "created_at": "2026-10-25T10:12:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

