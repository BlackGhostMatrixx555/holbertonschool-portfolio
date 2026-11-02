"""
Couche "services" : la logique métier de CampOrga.

Chaque service reçoit une session SQLAlchemy et des données déjà validées
par les schémas Pydantic. Il applique les règles métier (droits d'accès,
capacité d'un camp, doublons...) et lève des erreurs de app.core.exceptions.
Les routes (app/api) restent courtes : elles ne font que relier HTTP au service.
"""
