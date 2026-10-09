"""
Tests pour l'authentification JWT.

Couvre :
- POST /api/auth/login : succès, mauvais mot de passe, email inconnu, compte désactivé.
- Validation du token : token manquant, token invalide, token expiré.
- GET /api/users : accès autorisé (super_admin), refusé (autres rôles), sans token.
"""
from datetime import timedelta

from app.models import User, UserRole, UserStatus
from app.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------
def test_login_success(client, test_user):
    """Login avec bons identifiants → 200 + JWT."""
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "motdepasse123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_login_wrong_password(client, test_user):
    """Login avec mauvais mot de passe → 401."""
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "mauvais"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou mot de passe incorrect."


def test_login_unknown_email(client):
    """Login avec email inconnu → 401 + même message que mauvais mdp."""
    response = client.post(
        "/api/auth/login",
        json={"email": "inconnu@camporga.test", "password": "motdepasse123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou mot de passe incorrect."


def test_login_disabled_account(client, db_session):
    """Login avec compte désactivé → 401."""
    user = User(
        id=None,
        first_name="Désactivé",
        last_name="Test",
        email="disabled@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.DISABLED,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "disabled@camporga.test", "password": "motdepasse123"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Validation du token sur les routes protégées
# ---------------------------------------------------------------------------
def test_protected_route_without_token(client):
    """GET /api/users sans token → 401."""
    response = client.get("/api/users")
    assert response.status_code == 401


def test_protected_route_with_invalid_token(client):
    """GET /api/users avec token bidon → 401."""
    response = client.get(
        "/api/users",
        headers={"Authorization": "Bearer token-bidon"},
    )
    assert response.status_code == 401
    assert "invalide" in response.json()["detail"].lower()


def test_protected_route_with_expired_token(client, test_user):
    """GET /api/users avec token expiré → 401."""
    expired_token = create_access_token(
        subject=str(test_user.id),
        expires_delta=timedelta(minutes=-1),
    )
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_protected_route_with_unknown_user(client):
    """GET /api/users avec token valide mais user inexistant → 401."""
    token = create_access_token(subject="11111111-1111-1111-1111-111111111111")
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Gestion des rôles
# ---------------------------------------------------------------------------
def test_users_route_forbidden_for_non_admin(client, db_session):
    """GET /api/users avec un user non-super_admin → 403."""
    sem_user = User(
        id=None,
        first_name="SEM",
        last_name="User",
        email="sem@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    db_session.add(sem_user)
    db_session.commit()
    db_session.refresh(sem_user)

    token = create_access_token(subject=str(sem_user.id))
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "insuffisant" in response.json()["detail"].lower()


def test_users_route_allowed_for_super_admin(client, auth_headers):
    """GET /api/users avec super_admin → 200."""
    response = client.get("/api/users", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
