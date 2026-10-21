"""
Point d'entrée de l'API CampOrga.

Toutes les routes métier sont branchées ici sous le préfixe `/api`.
La documentation interactive est générée automatiquement par FastAPI
et accessible sur `/docs` (Swagger UI) et `/redoc` (ReDoc).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, backups, camps, chat, users

app = FastAPI(
    title="CampOrga API",
    description="API de gestion de summer camps de code & d'informatique",
    version="0.4.0",
)

# Autorise le frontend (React, sur un autre port) à appeler l'API en local.
# À restreindre à la vraie URL du frontend une fois en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes métier
app.include_router(camps.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(backups.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check():
    """Route simple pour vérifier que l'API répond."""
    return {"status": "ok"}
