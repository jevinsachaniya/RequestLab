"""Main application entry point for API Sentinel.

Initializes FastAPI, sets up middleware (CORS), and mounts routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router


def create_application() -> FastAPI:
    """Application factory that configures and returns the FastAPI app."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS (Cross-Origin Resource Sharing) middleware
    # Allows frontend (e.g. Vue on port 5173) to communicate with this backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include versioned API router under /api/v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    def root():
        """Root welcome endpoint with helpful navigation links."""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API!",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health",
            "version": settings.VERSION,
        }

    return app


app = create_application()

