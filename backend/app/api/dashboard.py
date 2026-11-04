"""Route du tableau de bord organisateur."""  # Docstring du module : route de synthèse affichée sur le tableau de bord.
from fastapi import APIRouter, Depends  # APIRouter pour grouper les routes, Depends pour l'injection de dépendances.
from sqlalchemy.orm import Session  # Type d'une session de base de données.

from app.core.deps import get_current_user  # Dépendance qui vérifie le jeton et renvoie l'utilisateur connecté.
from app.db.session import get_db  # Fournit une session de base de données.
from app.models import User  # Modèle utilisateur, utilisé pour typer l'utilisateur courant.
from app.schemas.dashboard import DashboardSummary  # Schéma de la réponse : la synthèse du tableau de bord.
from app.services import dashboard_service  # Couche service qui calcule la synthèse.

router = APIRouter(tags=["Tableau de bord"])  # Routeur sans préfixe, regroupé sous "Tableau de bord" dans la documentation Swagger.

@router.get("/dashboard/summary", response_model=DashboardSummary)  # Route GET /dashboard/summary : renvoie la synthèse, validée par le schéma DashboardSummary.
def dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):  # Utilisateur connecté (obligatoire) et session ; aucun paramètre dans l'URL.
    return dashboard_service.summary(db, current_user)  # Délègue le calcul au service en lui transmettant l'utilisateur, afin que la synthèse ne contienne que les données qu'il a le droit de voir.