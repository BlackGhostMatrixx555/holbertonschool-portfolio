"""
Point d'entrée de l'API CampOrga.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, camps, users

app = FastAPI(
    title="CampOrga API",
    description="API de gestion de summer camps de code & d'informatique",
    version="0.1.0",
)

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


@app.get("/health", tags=["health"])
def health_check():
    """Route simple pour vérifier que l'API répond."""
    return {"status": "ok"}
