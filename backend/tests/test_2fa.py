"""
Tests pour la double authentification (2FA).
"""
import pyotp

from app.models import User, UserRole, UserStatus
from app.security import hash_password


# ---------------------------------------------------------------------------
# POST /api/auth/2fa/setup
# ---------------------------------------------------------------------------
def test_setup_2fa(client, auth_headers):
    """POST /api/auth/2fa/setup → 200 + secret + QR code."""
    response = client.post("/api/auth/2fa/setup", headers=auth_headers)
    assert response.status_code == 200

    body = response.json()
    assert "secret" in body
    assert "otpauth_url" in body
    assert "qr_code_base64" in body
    assert body["otpauth_url"].startswith("otpauth://totp/")
    assert len(body["secret"]) > 0


def test_setup_2fa_without_auth(client):
    """POST /api/auth/2fa/setup sans token → 401."""
    response = client.post("/api/auth/2fa/setup")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/2fa/enable
# ---------------------------------------------------------------------------
def test_enable_2fa_with_valid_code(client, auth_headers):
    """POST /api/auth/2fa/enable avec un code valide → 200 + 2FA activée."""
    # 1. Récupérer le secret via setup
    setup_response = client.post("/api/auth/2fa/setup", headers=auth_headers)
    secret = setup_response.json()["secret"]

    # 2. Générer un code TOTP valide avec pyotp
    totp = pyotp.TOTP(secret)
    code = totp.now()

    # 3. Activer la 2FA avec ce code
    response = client.post(
        "/api/auth/2fa/enable",
        json={"code": code},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "activée" in response.json()["message"].lower()


def test_enable_2fa_with_invalid_code(client, auth_headers):
    """POST /api/auth/2fa/enable avec un code invalide → 400."""
    client.post("/api/auth/2fa/setup", headers=auth_headers)

    response = client.post(
        "/api/auth/2fa/enable",
        json={"code": "000000"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "invalide" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/auth/login (avec 2FA activée)
# ---------------------------------------------------------------------------
def test_login_with_2fa_returns_temp_token(client, db_session):
    """Login avec 2FA activée → 200 + requires_2fa=True + temp_token."""
    # 1. Créer un user avec 2FA déjà activée
    user = User(
        id=None,
        first_name="2FA",
        last_name="User",
        email="2fa@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
        is_2fa_enabled=True,
        totp_secret=pyotp.random_base32(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 2. Login avec mot de passe
    response = client.post(
        "/api/auth/login",
        json={"email": "2fa@camporga.test", "password": "motdepasse123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["requires_2fa"] is True
    assert body["temp_token"] is not None
    assert body["access_token"] is None


# ---------------------------------------------------------------------------
# POST /api/auth/2fa/login (étape 2 du login)
# ---------------------------------------------------------------------------
def test_login_2fa_success(client, db_session):
    """POST /api/auth/2fa/login avec un code valide → 200 + vrai JWT."""
    # 1. Créer un user avec 2FA activée
    secret = pyotp.random_base32()
    user = User(
        id=None,
        first_name="2FA",
        last_name="User",
        email="2fa-login@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
        is_2fa_enabled=True,
        totp_secret=secret,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 2. Login (étape 1) → récupérer le temp_token
    login_response = client.post(
        "/api/auth/login",
        json={"email": "2fa-login@camporga.test", "password": "motdepasse123"},
    )
    temp_token = login_response.json()["temp_token"]

    # 3. Générer un code TOTP valide
    totp = pyotp.TOTP(secret)
    code = totp.now()

    # 4. Valider le code (étape 2)
    response = client.post(
        "/api/auth/2fa/login",
        json={"temp_token": temp_token, "code": code},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] is not None
    assert body["token_type"] == "bearer"


def test_login_2fa_invalid_code(client, db_session):
    """POST /api/auth/2fa/login avec un code invalide → 401."""
    secret = pyotp.random_base32()
    user = User(
        id=None,
        first_name="2FA",
        last_name="User",
        email="2fa-invalid@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
        is_2fa_enabled=True,
        totp_secret=secret,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    login_response = client.post(
        "/api/auth/login",
        json={"email": "2fa-invalid@camporga.test", "password": "motdepasse123"},
    )
    temp_token = login_response.json()["temp_token"]

    response = client.post(
        "/api/auth/2fa/login",
        json={"temp_token": temp_token, "code": "000000"},
    )
    assert response.status_code == 401
    assert "invalide" in response.json()["detail"].lower()


def test_login_2fa_invalid_temp_token(client):
    """POST /api/auth/2fa/login avec un temp_token bidon → 401."""
    response = client.post(
        "/api/auth/2fa/login",
        json={"temp_token": "token-bidon", "code": "123456"},
    )
    assert response.status_code == 401
    assert "invalide" in response.json()["detail"].lower()
