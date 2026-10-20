"""
Tests pour les endpoints `/api/backups`.

Couvre :
- POST /api/backups : création SQL, création CSV, format invalide, non authentifié, non super admin.
- GET  /api/backups : liste (vide, avec données).
- GET  /api/backups/{id}/download : téléchargement (succès, 404).
"""
import io
import uuid
import zipfile
from pathlib import Path

import pytest

from app.models import User, UserRole, UserStatus
from app.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# POST /api/backups — création
# ---------------------------------------------------------------------------
def test_create_backup_sql(client, auth_headers):
    """POST /api/backups avec format=sql → 201 + fichier créé."""
    response = client.post(
        "/api/backups",
        json={"format": "sql"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    body = response.json()
    assert body["format"] == "sql"
    assert body["file_size_kb"] > 0
    assert "backup_" in body["file_path"]
    assert body["file_path"].endswith(".sql")

    # Le fichier doit exister sur le disque.
    file_path = Path(body["file_path"])
    assert file_path.exists()


def test_create_backup_csv(client, auth_headers):
    """POST /api/backups avec format=csv → 201 + fichier ZIP créé."""
    response = client.post(
        "/api/backups",
        json={"format": "csv"},
        headers=auth_headers,
    )
    assert response.status_code == 201

    body = response.json()
    assert body["format"] == "csv"
    assert body["file_path"].endswith(".csv")

    # Vérifier que le fichier est bien un ZIP valide
    file_path = Path(body["file_path"])
    assert file_path.exists()
    with zipfile.ZipFile(file_path, "r") as zf:
        # Le ZIP doit contenir au moins une entrée (les CSV des tables)
        names = zf.namelist()
        assert len(names) > 0
        # Chaque entrée doit être un fichier .csv
        assert all(name.endswith(".csv") for name in names)


def test_create_backup_invalid_format(client, auth_headers):
    """POST /api/backups avec format invalide → 422."""
    response = client.post(
        "/api/backups",
        json={"format": "pdf"},  # format non supporté
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_backup_without_auth(client):
    """POST /api/backups sans token → 401."""
    response = client.post("/api/backups", json={"format": "sql"})
    assert response.status_code == 401


def test_create_backup_forbidden_for_non_admin(client, db_session):
    """POST /api/backups avec un user non-super_admin → 403."""
    # Créer un user SEM (non super_admin)
    sem_user = User(
        id=None,
        first_name="SEM",
        last_name="User",
        email="sem-backup@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    db_session.add(sem_user)
    db_session.commit()
    db_session.refresh(sem_user)

    token = create_access_token(subject=str(sem_user.id))
    response = client.post(
        "/api/backups",
        json={"format": "sql"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/backups — liste
# ---------------------------------------------------------------------------
def test_list_backups_empty(client, auth_headers):
    """GET /api/backups sur une base vide → 200 + []."""
    response = client.get("/api/backups", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_backups_returns_created(client, auth_headers):
    """GET /api/backups retourne les backups créés."""
    # Créer 2 backups
    client.post("/api/backups", json={"format": "sql"}, headers=auth_headers)
    client.post("/api/backups", json={"format": "csv"}, headers=auth_headers)

    response = client.get("/api/backups", headers=auth_headers)
    assert response.status_code == 200
    backups = response.json()
    assert len(backups) == 2
    # Le plus récent en premier
    formats = {b["format"] for b in backups}
    assert formats == {"sql", "csv"}


def test_list_backups_without_auth(client):
    """GET /api/backups sans token → 401."""
    response = client.get("/api/backups")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/backups/{id}/download — téléchargement
# ---------------------------------------------------------------------------
def test_download_backup_success(client, auth_headers):
    """GET /api/backups/{id}/download → 200 + fichier."""
    # Créer un backup
    create_response = client.post(
        "/api/backups",
        json={"format": "sql"},
        headers=auth_headers,
    )
    backup_id = create_response.json()["id"]

    # Télécharger
    response = client.get(
        f"/api/backups/{backup_id}/download",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "").lower()
    # Le contenu ne doit pas être vide
    assert len(response.content) > 0


def test_download_backup_not_found(client, auth_headers):
    """GET /api/backups/{id}/download avec UUID inexistant → 404."""
    fake_id = uuid.uuid4()
    response = client.get(
        f"/api/backups/{fake_id}/download",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Backup introuvable."


def test_download_backup_without_auth(client):
    """GET /api/backups/{id}/download sans token → 401."""
    fake_id = uuid.uuid4()
    response = client.get(f"/api/backups/{fake_id}/download")
    assert response.status_code == 401
