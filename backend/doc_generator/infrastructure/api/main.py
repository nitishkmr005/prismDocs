"""FastAPI application for document generation.

Optimized for fast startup on cloud platforms (Render, etc.)
by deferring heavy imports until first request.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Flag to track if heavy routes are loaded
_routes_initialized = False


def _init_heavy_routes(app: FastAPI) -> None:
    """Initialize heavy routes on first request (lazy loading)."""
    global _routes_initialized
    if _routes_initialized:
        return

    # Import and initialize logging
    from ..logging_config import setup_logging

    setup_logging(verbose=True)

    # Import heavy route modules (these load large deps, etc.)
    from .routes import (
        cache_router,
        download_router,
        generate_router,
        idea_canvas_router,
        image_router,
        mindmap_router,
        podcast_router,
        upload_router,
    )

    # Include heavy routers
    app.include_router(upload_router, prefix="/api")
    app.include_router(generate_router, prefix="/api")
    app.include_router(download_router, prefix="/api")
    app.include_router(cache_router, prefix="/api")
    app.include_router(image_router, prefix="/api")
    app.include_router(mindmap_router, prefix="/api")
    app.include_router(idea_canvas_router, prefix="/api")
    app.include_router(podcast_router, prefix="/api")

    _routes_initialized = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup: only log that we're ready (no heavy imports here)
    print("==> PrismDocs API ready to receive requests", flush=True)
    yield
    # Shutdown
    print("==> PrismDocs API shutting down", flush=True)


app = FastAPI(
    title="PrismDocs API",
    description="Generate PDF and PPTX documents from multiple sources with PrismDocs",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lightweight health check - loads immediately (no heavy deps)
@app.get("/api/health", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "service": "prismdocs"}


# Middleware to initialize heavy routes on first non-health request
@app.middleware("http")
async def lazy_init_middleware(request, call_next):
    """Initialize heavy routes on first non-health request."""
    if not _routes_initialized and request.url.path != "/api/health":
        _init_heavy_routes(app)
    return await call_next(request)
