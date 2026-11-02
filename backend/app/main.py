"""
Point d'entrée de l'API CampOrga.

Assemble l'application : middleware CORS, gestion des erreurs métier,
routeurs de chaque domaine et routes de supervision (health / ready).
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.api import auth, backups, camps, contact_messages, dashboard, landing_pages, registrations, users
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import engine

app = FastAPI(
    title="CampOrga API",
    version="0.2.0",
    description="API de gestion de summer camps de code : camps, landing pages, inscriptions.",
)

# CORS : seul le front-end déclaré dans la configuration peut appeler l'API
# depuis un navigateur. Les en-têtes autorisés sont limités au strict nécessaire.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(AppError)
def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    """Traduit une erreur métier (NotFoundError, ConflictError...) en réponse HTTP."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Toutes les routes métier sont préfixées par /api.
for module in (auth, users, camps, registrations, landing_pages, contact_messages, dashboard, backups):
    app.include_router(module.router, prefix="/api")


@app.get("/", tags=["Supervision"])
def read_root():
    return {"message": "Welcome to CampOrga API"}


@app.get("/health", tags=["Supervision"])
def health_check():
    """Liveness : le processus répond."""
    return {"status": "ok"}


@app.get("/ready", tags=["Supervision"])
def readiness_check():
    """Readiness : la base de données répond aussi (utilisé par Docker)."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc
    return {"status": "ready", "database": "connected"}
