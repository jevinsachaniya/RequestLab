"""Version 1 API router aggregator.

Combines all sub-routers (health, auth, collections, requests, etc.) into one router.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, collections, auth, requests, history

api_router = APIRouter()

# Register health check endpoint under /api/v1
api_router.include_router(health.router, tags=["Health"])

# Register authentication endpoints under /api/v1/auth
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Register collections endpoints under /api/v1/collections
api_router.include_router(
    collections.router, prefix="/collections", tags=["Collections"]
)

# Register saved requests and request execution endpoints under /api/v1
api_router.include_router(
    requests.router, tags=["Saved Requests & Execution"]
)

# Register execution history endpoints under /api/v1/history
api_router.include_router(
    history.router, prefix="/history", tags=["Execution History"]
)





