from io import BytesIO
from zipfile import ZipFile

from app.core.security import create_access_token
from app.models import User, UserRole, UserStatus
from app.core.security import hash_password


def test_super_admin_can_export_csv_archive(client, auth_headers):
    response = client.get("/api/admin/backups?format=csv", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(response.content)) as archive:
        assert {"users.csv", "camps.csv", "registrations.csv"}.issubset(archive.namelist())
        assert "password_hash" in archive.read("users.csv").decode()


def test_non_admin_cannot_export_backup(client, db_session):
    user = User(
        email="backup-denied@example.test",
        password_hash=hash_password("secure-test-password"),
        role=UserRole.ORGANIZER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(subject=str(user.id))

    response = client.get(
        "/api/admin/backups?format=csv",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

# ---- Export SQL (pg_dump simulé : le test ne dépend pas de l'outil installé) ----

def test_super_admin_can_export_sql_dump(client, auth_headers, monkeypatch):
    import subprocess

    def fake_run(command, **kwargs):
        # pg_dump écrit dans le fichier passé après --file
        path = command[command.index("--file") + 1]
        with open(path, "w") as dump:
            dump.write("-- PostgreSQL database dump\nCREATE TABLE camps ();\n")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("app.services.backup_service.subprocess.run", fake_run)
    response = client.get("/api/admin/backups?format=sql", headers=auth_headers)

    assert response.status_code == 200
    assert "CREATE TABLE camps" in response.text


def test_sql_dump_failure_returns_503(client, auth_headers, monkeypatch):
    import subprocess

    def failing_run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("app.services.backup_service.subprocess.run", failing_run)
    response = client.get("/api/admin/backups?format=sql", headers=auth_headers)
    assert response.status_code == 503


def test_unknown_backup_format_is_rejected(client, auth_headers):
    assert client.get("/api/admin/backups?format=xml", headers=auth_headers).status_code == 422
