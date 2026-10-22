"""
Tests pour l'authentification JWT.

Couvre :
- POST /api/auth/login : succès, mauvais mot de passe, email inconnu, compte désactivé.
- POST /api/auth/register : succès, email dupliqué, mot de passe court.
- Validation du token : token manquant, token invalide, token expiré.
- GET /api/users : accès autorisé (super_admin), refusé (autres rôles), sans token.
- DELETE /api/users/me : succès (SEM), refusé pour super admin (éternel), sans token.
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
# POST /api/auth/register
# ---------------------------------------------------------------------------
def test_register_success(client):
    """POST /api/auth/register → 201 + user créé avec rôle SEM."""
    payload = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@camporga.test",
        "password": "MotDePasse123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "jean.dupont@camporga.test"
    assert body["role"] == "sem"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email(client, test_user):
    """POST /api/auth/register avec un email déjà pris → 409."""
    payload = {
        "first_name": "Tété",
        "last_name": "Dufrénoy",
        "email": test_user.email,
        "password": "MotDePasse123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert "existe déjà" in response.json()["detail"]


def test_register_short_password(client):
    """POST /api/auth/register avec mot de passe trop court → 422."""
    payload = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean2@camporga.test",
        "password": "court",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


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


# ---------------------------------------------------------------------------
# DELETE /api/users/me
# ---------------------------------------------------------------------------
def test_delete_my_account(client, db_session):
    """DELETE /api/users/me avec un compte non-admin → 204 + compte supprimé."""
    sem_user = User(
        id=None,
        first_name="SEM",
        last_name="User",
        email="sem-delete@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    db_session.add(sem_user)
    db_session.commit()
    db_session.refresh(sem_user)

    token = create_access_token(subject=str(sem_user.id))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete("/api/users/me", headers=headers)
    assert response.status_code == 204

    login_response = client.post(
        "/api/auth/login",
        json={"email": "sem-delete@camporga.test", "password": "motdepasse123"},
    )
    assert login_response.status_code == 401


def test_delete_my_account_forbidden_for_super_admin(client, auth_headers):
    """DELETE /api/users/me avec un super admin → 403 (éternel)."""
    response = client.delete("/api/users/me", headers=auth_headers)
    assert response.status_code == 403
    assert "éternel" in response.json()["detail"].lower()


def test_delete_my_account_without_auth(client):
    """DELETE /api/users/me sans token → 401."""
    response = client.delete("/api/users/me")
    assert response.status_code == 401
