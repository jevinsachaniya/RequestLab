# 🛡️ API Sentinel — Mini Postman

A secure, simplified, full-stack API testing platform inspired by Postman. Built with **FastAPI**, **SQLAlchemy 2.x**, **Pydantic v2**, and **Vue.js 3 + Vuetify**, designed to demonstrate senior backend engineering practices, robust defensive security against Server-Side Request Forgery (SSRF), multi-tenant ownership isolation, and automated response assertions.

---

## 🌟 Key Features

* **User Authentication & Authorization:**
  * User registration and login with salt-hashed passwords via `bcrypt` (12 rounds).
  * Stateless HMAC-SHA256 JWT access tokens with configurable expiration (default 60 minutes).
  * Strict multi-tenant user isolation on all collections, saved requests, and execution logs.
* **Collections & Request Management:**
  * Full CRUD management for API collections and nested saved requests.
  * Support for HTTP methods: `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`.
  * Configurable query parameters, headers, and JSON request bodies.
* **Defensive HTTP Request Execution Engine:**
  * Outbound HTTP client powered by asynchronous `httpx`.
  * **SSRF Protection:** Pre-flight DNS resolution blocks loopback (`127.0.0.0/8`, `::1`), private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata IP addresses (`169.254.169.254`, `100.100.100.200`).
  * **Safe Redirects:** Redirects are disabled by default. When enabled, each hop is re-validated through the SSRF engine, and `Authorization` headers are stripped across foreign domains.
  * **Resource Guards:** Configurable timeouts (10s) and streaming response size capping (5 MB) to prevent denial-of-service memory exhaustion.
* **Automated Response Assertions:**
  * Built-in assertion engine evaluating status codes, response time thresholds, headers, and nested JSON fields (using safe dot-notation like `data.user.id` without `eval()`).
* **Execution History & Audit Trail:**
  * Automatic logging of request executions, status codes, response headers, response bodies, and latency.
  * Automatic redaction of sensitive credentials (`Authorization`, `Cookie`, `X-Api-Key`).
* **Modern Vue.js 3 Frontend:**
  * Clean, responsive single-page application built with Vite and Vuetify 3 (Material Design).
  * Features collection explorer, dynamic request builder, formatted JSON response viewer, test results display, and history drawer.

---

## 🏗️ Architecture & Project Structure

```text
API_Checker/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Dependency injection (get_db, get_current_user)
│   │   │   └── v1/
│   │   │       ├── endpoints/        # auth, collections, requests, history, health
│   │   │       └── router.py         # Versioned v1 API router aggregator
│   │   ├── core/
│   │   │   ├── config.py             # App settings (Pydantic BaseSettings)
│   │   │   ├── security.py           # Bcrypt hashing & PyJWT token utilities
│   │   │   └── ssrf.py               # SSRF DNS validator & IP blacklist guards
│   │   ├── db/
│   │   │   ├── base_class.py         # SQLAlchemy 2.0 DeclarativeBase
│   │   │   └── session.py            # SQLite engine & session factory
│   │   ├── models/                   # ORM models (User, Collection, SavedRequest, RequestExecution)
│   │   ├── repositories/             # Data access layer with user ownership filtering
│   │   ├── schemas/                  # Pydantic v2 validation & response models
│   │   ├── services/                 # Business logic, HTTP executor, Assertion engine
│   │   └── main.py                   # FastAPI app factory, CORS middleware, OpenAPI config
│   ├── alembic/                      # Database migrations
│   ├── tests/                        # 72 automated pytest suites (isolated in-memory DB)
│   ├── requirements.txt              # Pinned backend dependencies
│   ├── alembic.ini                   # Alembic configuration
│   └── .env.example                  # Template configuration
├── frontend/
│   ├── src/
│   │   ├── api/client.js             # Axios client with JWT bearer interceptor
│   │   ├── components/               # Vue components (Sidebar, Builder, Viewer, History, Dialogs)
│   │   ├── stores/appState.js        # Reactive state store
│   │   ├── plugins/vuetify.js        # Vuetify theme and icons
│   │   ├── App.vue                   # Application shell
│   │   └── main.js                   # Vue entrypoint
│   ├── package.json                  # Frontend dependencies
│   ├── vite.config.js                # Vite build config
│   └── .env.example                  # Frontend API URL configuration
├── docs/
│   ├── architecture.md               # Detailed system architecture & threat model
│   └── sample_workflow.md            # Step-by-step cURL workflow guide
├── pytest.ini                        # Pytest settings and import paths
├── .gitignore                        # Git exclusion rules
└── README.md                         # Project documentation
```

---

## 🛠️ Technology Stack

* **Backend:**
  * **Language:** Python 3.13
  * **Framework:** FastAPI
  * **Data Validation:** Pydantic v2 & Pydantic-Settings
  * **Database & ORM:** SQLite, SQLAlchemy 2.x
  * **Migrations:** Alembic
  * **Security & Auth:** PyJWT, Bcrypt
  * **HTTP Client:** HTTPX (async client with streaming)
  * **Testing:** Pytest, Pytest-Asyncio
* **Frontend:**
  * **Framework:** Vue.js 3 (Composition API)
  * **Tooling:** Vite
  * **UI Component Library:** Vuetify 3 (Material Design Icons)
  * **HTTP Client:** Axios

---

## 🚀 Getting Started (Windows PowerShell Setup)

### 1. Prerequisites
* **Python 3.12+** (tested on Python 3.13.5)
* **Node.js 20+** (tested on Node.js v24.14.0) and **npm**
* **Git**

### 2. Clone and Configure Backend
```powershell
# Navigate into the project folder
cd "API_Checker"

# Create Python virtual environment
python -m venv backend\.venv

# Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt

# Copy environment variables
Copy-Item backend\.env.example backend\.env
```

### 3. Run Database Migrations
```powershell
# Apply Alembic database migrations to head
.\backend\.venv\Scripts\python.exe -m alembic upgrade head
```

### 4. Install Frontend Dependencies
```powershell
# Copy frontend environment file
Copy-Item frontend\.env.example frontend\.env

# Install frontend packages
npm install --prefix frontend
```

---

## 💻 Running the Application

Open two separate Windows PowerShell terminals:

### Terminal 1 — Start the Backend Server:
```powershell
$env:PYTHONPATH = "backend"
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
* **Interactive OpenAPI Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **Health Check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Terminal 2 — Start the Frontend Development Server:
```powershell
npm run dev --prefix frontend
```
* **Frontend Application UI:** [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 🧪 Automated Testing

The backend includes a comprehensive automated test suite with **72 test cases** covering authentication, CRUD, cascade deletions, SSRF defenses, timeouts, response assertions, and execution history.

Outbound HTTP calls are mocked; tests run 100% offline using an isolated in-memory SQLite database without modifying development data.

```powershell
# Run all tests with verbose output
.\backend\.venv\Scripts\python.exe -m pytest -v
```

### Test Suite Breakdown:
* `test_auth.py` (10 tests): User registration, duplicate email rejection, bcrypt verification, JWT generation, expired tokens, unauthorized access, cross-user isolation.
* `test_collections.py` (9 tests): Collection CRUD, pagination parameters, 404 handling, user scoping.
* `test_ssrf.py` (26 tests): Validating blocking of 127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, cloud metadata (`169.254.169.254`), dangerous hostnames, and unsupported protocols (`file://`, `ftp://`).
* `test_requests.py` (12 tests): Saved request CRUD, cascade deletion, execution engine, timeouts, mocked GET/POST calls.
* `test_history_and_assertions.py` (8 tests): JSON path extraction, status assertions, latency thresholds, JSON field comparisons, header redaction, and history pagination.
* `test_models.py` (4 tests): SQLAlchemy ORM models, unique constraints, and foreign key relationships.
* `test_health.py` (3 tests): Health check, root endpoint, and Swagger schema accessibility.

---

## 🔒 Security Architecture & Defensive Design

1. **SSRF Guard (`app/core/ssrf.py`):**
   * Pre-resolves hostnames before HTTP socket connection.
   * Checks every resolved IPv4 and IPv6 address against private, loopback, link-local, multicast, and cloud metadata ranges (`169.254.169.254`).
   * Re-evaluates target URLs upon HTTP 3xx redirects and strips `Authorization` headers on cross-domain redirects.
2. **Resource Exhaustion Limits:**
   * Maximum response size strictly enforced at 5 MB via response streaming (`aiter_bytes`).
   * Maximum outbound request timeout fixed at 10 seconds.
   * Stored response bodies in database truncated to 250 KB.
3. **Multi-Tenant Data Privacy:**
   * Queries strictly scope `Collection.user_id == current_user.id` and `SavedRequest.user_id == current_user.id`.
   * Unauthorized cross-user requests return `404 Not Found` rather than `403 Forbidden` to prevent resource ID enumeration attacks.
4. **Secret Management:**
   * Secret keys and configuration are loaded from environment variables using `pydantic-settings`.
   * `.env`, SQLite databases (`*.db`), `.venv`, and `node_modules` are excluded from version control via `.gitignore`.
   * Execution history automatically masks sensitive headers (`Authorization`, `Cookie`, `X-Api-Key`).

---

## ⚠️ Known Limitations & Future Improvements

* **Distributed Rate Limiting:** The local implementation relies on timeouts and size limits. A production deployment in a container cluster should add Redis-backed rate limiting (e.g. `slowapi` or Redis token bucket) to enforce requests-per-minute quotas per user.
* **PostgreSQL in Production:** SQLite is used for lightweight local development. For high-concurrency production deployments, swap `DATABASE_URL` in `.env` to `postgresql+psycopg2://user:pass@host/db`; the SQLAlchemy models and Alembic migrations are written to be fully PostgreSQL-compatible.
* **Collection Import/Export:** Future enhancements can support importing and exporting Postman Collection v2.1 JSON files.
* **Environment Variables in Requests:** Support Postman-style variable templating (e.g. `{{base_url}}/users`).

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

#   R e q u e s t L a b  
 