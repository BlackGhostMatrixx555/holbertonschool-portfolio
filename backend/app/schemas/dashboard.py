"""Schémas du tableau de bord organisateur."""  # Docstring du module : schémas du tableau de bord organisateur.
from datetime import datetime  # Type des dates et heures, utilisé pour la date de création des inscriptions.
from uuid import UUID  # Type des identifiants (inscription, camp).

from pydantic import BaseModel  # Classe de base Pydantic pour la validation et la sérialisation.

class CampCounts(BaseModel):  # Compteurs des camps de l'organisateur par statut.
    total: int  # Nombre total de camps.
    draft: int  # Nombre de camps en brouillon.
    published: int  # Nombre de camps publiés.
    archived: int  # Nombre de camps archivés.

class RegistrationCounts(BaseModel):  # Compteurs des inscriptions.
    total: int  # Nombre total d'inscriptions.

class RecentRegistration(BaseModel):  # Une inscription récente affichée sur le tableau de bord.
    id: UUID  # Identifiant de l'inscription.
    camp_id: UUID  # Identifiant du camp concerné.
    first_name: str  # Prénom de l'inscrit.
    last_name: str  # Nom de l'inscrit.
    email: str  # Adresse email de l'inscrit.
    created_at: datetime | None  # Date de création de l'inscription, pouvant être vide.

class DashboardSummary(BaseModel):  # Synthèse complète renvoyée au tableau de bord.
    camps: CampCounts  # Compteurs des camps.
    registrations: RegistrationCounts  # Compteurs des inscriptions.
    recent_registrations: list[RecentRegistration]  # Liste des inscriptions les plus récentes.