"""
Application entrypoint.

Wires together: DB table creation, routers, CORS, and a global exception
handler so unexpected errors return a clean JSON response instead of a
raw traceback.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


app.include_router(auth.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(enrollments.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
