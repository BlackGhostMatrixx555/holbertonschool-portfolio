"""
Tests de l'historique des sauvegardes (fusion collins + tete-work) :
création SQL / CSV, liste, téléchargement, droits d'accès.
"""
import subprocess
import uuid
from io import BytesIO
from zipfile import ZipFile

from app.core.security import create_access_token, hash_password
from app.models import User, UserRole, UserStatus


def _fake_pg_dump(monkeypatch):
    """Simule pg_dump : le test ne dépend pas de l'outil installé."""

    def fake_run(command, **kwargs):
        path = command[command.index("--file") + 1]
        with open(path, "w") as dump:
            dump.write("-- PostgreSQL database dump\nCREATE TABLE camps ();\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("app.services.backup_service.subprocess.run", fake_run)


def _organizer_headers(db_session):
    user = User(
        email="backup-denied@example.com",
        password_hash=hash_password("secure-test-password"),
        role=UserRole.ORGANIZER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def test_create_csv_backup_then_download_zip(client, auth_headers):
    created = client.post("/api/backups", json={"format": "csv"}, headers=auth_headers)
    assert created.status_code == 201
    body = created.json()
    assert body["format"] == "csv" and body["file_size_kb"] >= 1
    assert "file_path" not in body  # le chemin sur le serveur n'est pas exposé

    download = client.get(f"/api/backups/{body['id']}/download", headers=auth_headers)
    assert download.status_code == 200
    with ZipFile(BytesIO(download.content)) as archive:
        assert {"users.csv", "camps.csv", "registrations.csv", "backups.csv"}.issubset(archive.namelist())


def test_create_sql_backup(client, auth_headers, monkeypatch):
    _fake_pg_dump(monkeypatch)
    created = client.post("/api/backups", json={"format": "sql"}, headers=auth_headers)
    assert created.status_code == 201
    download = client.get(f"/api/backups/{created.json()['id']}/download", headers=auth_headers)
    assert "CREATE TABLE camps" in download.text


def test_sql_dump_failure_returns_503_and_records_nothing(client, auth_headers, monkeypatch):
    def failing_run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("app.services.backup_service.subprocess.run", failing_run)
    assert client.post("/api/backups", json={"format": "sql"}, headers=auth_headers).status_code == 503
    assert client.get("/api/backups", headers=auth_headers).json() == []


def test_history_lists_backups_newest_first(client, auth_headers):
    first = client.post("/api/backups", json={"format": "csv"}, headers=auth_headers).json()
    second = client.post("/api/backups", json={"format": "csv"}, headers=auth_headers).json()
    history = client.get("/api/backups", headers=auth_headers).json()
    assert {item["id"] for item in history} == {first["id"], second["id"]}


def test_unknown_format_is_rejected(client, auth_headers):
    assert client.post("/api/backups", json={"format": "xml"}, headers=auth_headers).status_code == 422


def test_download_unknown_backup_returns_404(client, auth_headers):
    assert client.get(f"/api/backups/{uuid.uuid4()}/download", headers=auth_headers).status_code == 404


def test_download_returns_410_when_file_was_removed(client, auth_headers, backup_dir):
    backup = client.post("/api/backups", json={"format": "csv"}, headers=auth_headers).json()
    for file in backup_dir.iterdir():
        file.unlink()
    assert client.get(f"/api/backups/{backup['id']}/download", headers=auth_headers).status_code == 410


def test_backups_are_forbidden_for_organizers(client, db_session):
    headers = _organizer_headers(db_session)
    assert client.post("/api/backups", json={"format": "csv"}, headers=headers).status_code == 403
    assert client.get("/api/backups", headers=headers).status_code == 403


def test_backups_require_authentication(client):
    assert client.get("/api/backups").status_code == 401
