from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.camps import router as camps_router
from app.api.registrations import router as registrations_router
from app.api.landing_pages import router as landing_pages_router
from app.api.contact_messages import router as contact_messages_router
from app.api.dashboard import router as dashboard_router
from app.api.backups import router as backups_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title="CampOrga API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(camps_router, prefix="/api")
app.include_router(registrations_router, prefix="/api")
app.include_router(landing_pages_router, prefix="/api")
app.include_router(contact_messages_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(backups_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to CampOrga API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc
    return {"status": "ready", "database": "connected"}
