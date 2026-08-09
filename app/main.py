"""
Application entrypoint.

Wires together: DB table creation, routers, CORS, a global exception
handler, and the static frontend -- in that order. Route order matters:
Starlette matches routes top-to-bottom, so the API routers are registered
first (they own /auth, /students, /courses, /enrollments, /health) and the
StaticFiles mount at "/" is registered last, acting as a catch-all for
everything else (the SPA's index.html, style.css, app.js). This is what
makes both "the frontend loads at /" and "the API still works" true at
the same time.
"""
import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, students, courses, enrollments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sms")

# Creates tables on startup if they don't exist yet. For a production system
# you'd swap this for Alembic migrations (already scaffolded in /alembic).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Student Management System API",
    description="A role-based REST API for managing students, courses, and enrollments.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# --- API routers (registered first, so they take precedence over the
#     static catch-all mounted below) ---
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(enrollments.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


# --- Frontend ---
# html=True makes StaticFiles serve index.html both for "/" and for any
# unmatched sub-path (client-side routing friendly), instead of 404ing.
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static-assets")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
