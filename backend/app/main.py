"""
Point d'entrée de l'API CampOrga.
"""
# On importe la classe FastAPI, qui permet de créer l'application web
from fastapi import FastAPI
# On importe le middleware CORS, qui gère les requêtes venant d'un autre domaine (ici le frontend)
from fastapi.middleware.cors import CORSMiddleware

# On importe tous les modules de routes (chaque module contient un groupe d'endpoints)
from app.routes import auth, backups, camps, chat, payments, two_factor, users, verification

# On crée l'application FastAPI avec ses métadonnées (affichées dans la doc Swagger)
app = FastAPI(
    # Titre de l'API affiché dans /docs
    title="CampOrga API",
    # Description de l'API affichée dans /docs
    description="API de gestion de summer camps de code & d'informatique",
    # Numéro de version de l'API
    version="0.7.0",
# Fin de la création de l'application
)

# On ajoute le middleware CORS à l'application
app.add_middleware(
    # Type de middleware à ajouter
    CORSMiddleware,
    # Seule l'origine du frontend en développement (Vite, port 5173) est autorisée à appeler l'API
    allow_origins=["http://localhost:5173"],
    # On autorise l'envoi des cookies et des en-têtes d'authentification
    allow_credentials=True,
    # On autorise toutes les méthodes HTTP (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # On autorise tous les en-têtes HTTP dans les requêtes
    allow_headers=["*"],
# Fin de la configuration du middleware CORS
)

# Routes métier
# On branche les routes des camps, sous le préfixe /api
app.include_router(camps.router, prefix="/api")
# On branche les routes d'authentification (connexion, etc.), sous le préfixe /api
app.include_router(auth.router, prefix="/api")
# On branche les routes de gestion des utilisateurs, sous le préfixe /api
app.include_router(users.router, prefix="/api")
# On branche les routes des sauvegardes (backups SQL/CSV), sous le préfixe /api
app.include_router(backups.router, prefix="/api")
# On branche les routes du chatbot, sous le préfixe /api
app.include_router(chat.router, prefix="/api")
# On branche les routes de l'authentification à deux facteurs (2FA), sous le préfixe /api
app.include_router(two_factor.router, prefix="/api")
# On branche les routes de vérification (par exemple de l'email), sous le préfixe /api
app.include_router(verification.router, prefix="/api")
# On branche les routes de paiement, sous le préfixe /api
app.include_router(payments.router, prefix="/api")


# Décorateur : déclare une route GET sur /health, rangée sous le tag "health" dans la doc
@app.get("/health", tags=["health"])
# Fonction exécutée quand cette route est appelée
def health_check():
    """Route simple pour vérifier que l'API répond."""
    # On retourne un petit JSON indiquant que l'API fonctionne
    return {"status": "ok"}
