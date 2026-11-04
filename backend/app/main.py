"""
Point d'entrée de l'API CampOrga.

Assemble l'application : middleware CORS, gestion des erreurs métier,
routeurs de chaque domaine et routes de supervision (health / ready).
"""
import logging  # Module standard de journalisation (logs).
from contextlib import asynccontextmanager  # Décorateur pour écrire le cycle de vie de l'application (démarrage / arrêt).

from fastapi import FastAPI, HTTPException, Request  # Classe principale de l'application, exception HTTP et objet requête.
from fastapi.responses import JSONResponse  # Réponse HTTP au format JSON, avec un code de statut choisi.
from sqlalchemy import text  # Permet d'écrire une requête SQL brute, ici pour tester la connexion.
from sqlalchemy.exc import SQLAlchemyError  # Classe de base de toutes les erreurs SQLAlchemy.
from starlette.middleware.cors import CORSMiddleware  # Middleware CORS, qui gère les requêtes venant d'un autre domaine (le front-end).

from pymongo.errors import PyMongoError  # Classe de base des erreurs du driver MongoDB.

from app.api import auth, backups, camps, chat, contact_messages, dashboard, landing_pages, registrations, users  # Modules de routes de chaque domaine.
from app.core.config import settings  # Configuration globale de l'application (lue depuis l'environnement).
from app.core.exceptions import AppError  # Classe de base des erreurs métier de l'application.
from app.db.mongo import ensure_indexes, get_mongo_db  # Création des index MongoDB et fournisseur de la base MongoDB.
from app.db.session import engine  # Moteur SQLAlchemy, qui gère les connexions à la base relationnelle.

logger = logging.getLogger("camporga")  # Logger nommé « camporga » ; les messages apparaîtront avec ce nom dans les logs.

@asynccontextmanager  # Transforme la fonction en gestionnaire de contexte asynchrone, utilisé par FastAPI.
async def lifespan(application: FastAPI):  # Code exécuté au démarrage (avant le yield) et à l'arrêt (après le yield).
    """Au démarrage : crée les index MongoDB. L'API démarre même si MongoDB
    est indisponible : seul le chatbot sera inaccessible (réponse 503)."""
    # Respecte une éventuelle surcharge (les tests utilisent une base simulée).
    provider = application.dependency_overrides.get(get_mongo_db, get_mongo_db)  # Prend la version de test de get_mongo_db si elle est surchargée, sinon la version réelle.
    try:
        ensure_indexes(provider())  # Appelle le fournisseur pour obtenir la base, puis crée les index nécessaires.
    except PyMongoError as exc:  # MongoDB est injoignable ou une opération a échoué.
        logger.warning("MongoDB indisponible au démarrage : %s", exc)  # Journalise un avertissement sans arrêter l'application.
    yield  # Donne la main à l'application : elle tourne jusqu'à son arrêt.

app = FastAPI(  # Crée l'application FastAPI.
    lifespan=lifespan,  # Branche le gestionnaire de cycle de vie défini plus haut.
    title="CampOrga API",  # Titre affiché dans la documentation Swagger.
    version="0.2.0",  # Version de l'API.
    description="API de gestion de summer camps de code : camps, landing pages, inscriptions.",  # Description affichée dans la documentation.
)

# CORS : seul le front-end déclaré dans la configuration peut appeler l'API
# depuis un navigateur. Les en-têtes autorisés sont limités au strict nécessaire.
app.add_middleware(  # Ajoute le middleware CORS à l'application.
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Liste des origines (domaines) autorisées, lue dans la configuration.
    allow_credentials=True,  # Autorise l'envoi de cookies et d'en-têtes d'authentification.
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Méthodes HTTP autorisées depuis le navigateur.
    allow_headers=["Authorization", "Content-Type"],  # En-têtes de requête autorisés : le jeton et le type de contenu.
    # Sans cela, le navigateur cache cet en-tête au JavaScript (CORS) et le
    # front-end ne peut pas connaître le nom du fichier de sauvegarde téléchargé.
    expose_headers=["Content-Disposition"],  # Rend l'en-tête visible côté JavaScript, pour lire le nom du fichier.
)

@app.exception_handler(AppError)  # Enregistre la fonction ci-dessous comme gestionnaire de toutes les AppError.
def handle_app_error(_: Request, exc: AppError) -> JSONResponse:  # Le premier paramètre (la requête) n'est pas utilisé, d'où le nom « _ ».
    """Traduit une erreur métier (NotFoundError, ConflictError...) en réponse HTTP."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})  # Renvoie le code et le message définis dans l'erreur.

# Toutes les routes métier sont préfixées par /api.
for module in (auth, users, camps, registrations, landing_pages, contact_messages, chat, dashboard, backups):  # Parcourt chaque module de routes.
    app.include_router(module.router, prefix="/api")  # Branche les routes du module, sous le préfixe /api.

@app.get("/", tags=["Supervision"])  # Route GET à la racine ; le tag regroupe les routes dans la documentation.
def read_root():
    return {"message": "Welcome to CampOrga API"}  # Message d'accueil, permet de vérifier rapidement que l'API répond.

@app.get("/health", tags=["Supervision"])  # Route GET /health, utilisée pour la supervision.
def health_check():
    """Liveness : le processus répond."""  # Ne vérifie que le processus, pas les dépendances.
    return {"status": "ok"}  # Répond toujours OK si l'application tourne.

@app.get("/ready", tags=["Supervision"])  # Route GET /ready, vérifie que l'application peut réellement servir des requêtes.
def readiness_check():
    """Readiness : la base de données répond aussi (utilisé par Docker)."""
    try:
        with engine.connect() as connection:  # Ouvre une connexion à la base, fermée automatiquement à la sortie du bloc.
            connection.execute(text("SELECT 1"))  # Requête minimale : elle échoue si la base ne répond pas.
    except SQLAlchemyError as exc:  # La base est injoignable ou la requête a échoué.
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc  # Renvoie 503 (service indisponible) ; « from exc » garde l'erreur d'origine pour le débogage.
    return {"status": "ready", "database": "connected"}  # La base répond : l'application est prête.