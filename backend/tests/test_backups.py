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