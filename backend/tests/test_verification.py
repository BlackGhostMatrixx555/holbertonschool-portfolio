"""
Tests pour la vérification par SMS et Email (Mock).
"""
from app.models import User, UserRole, UserStatus
from app.security import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _create_user(db_session, email="verify@camporga.test", phone=None):
    """Crée un utilisateur de test avec ou sans numéro de téléphone."""
    user = User(
        id=None,
        first_name="Verify",
        last_name="User",
        email=email,
        phone_number=phone,
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# POST /api/auth/verify/send-email
# ---------------------------------------------------------------------------
def test_send_email_code(client, auth_headers):
    """POST /api/auth/verify/send-email → 200 + debug_code."""
    response = client.post("/api/auth/verify/send-email", headers=auth_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "debug_code" in body
    assert len(body["debug_code"]) == 6
    assert body["debug_code"].isdigit()


def test_send_email_without_auth(client):
    """POST /api/auth/verify/send-email sans token → 401."""
    response = client.post("/api/auth/verify/send-email")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/auth/verify/send-sms
# ---------------------------------------------------------------------------
def test_send_sms_without_phone(client, db_session):
    """POST /api/auth/verify/send-sms sans numéro → 400."""
    user = _create_user(db_session, email="nophone@camporga.test")
    from app.security import create_access_token
    token = create_access_token(subject=str(user.id))

    response = client.post(
        "/api/auth/verify/send-sms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "téléphone" in response.json()["detail"].lower()


def test_send_sms_with_phone(client, db_session):
    """POST /api/auth/verify/send-sms avec numéro → 200 + debug_code."""
    user = _create_user(
        db_session,
        email="withphone@camporga.test",
        phone="+33612345678",
    )
    from app.security import create_access_token
    token = create_access_token(subject=str(user.id))

    response = client.post(
        "/api/auth/verify/send-sms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "debug_code" in body
    assert len(body["debug_code"]) == 6


# ---------------------------------------------------------------------------
# POST /api/auth/verify/check-code
# ---------------------------------------------------------------------------
def test_check_code_valid(client, auth_headers):
    """POST /api/auth/verify/check-code avec code valide → 200."""
    # 1. Demander un code par email
    send_response = client.post(
        "/api/auth/verify/send-email",
        headers=auth_headers,
    )
    code = send_response.json()["debug_code"]

    # 2. Valider le code
    response = client.post(
        "/api/auth/verify/check-code",
        json={"code": code},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_check_code_invalid(client, auth_headers):
    """POST /api/auth/verify/check-code avec code invalide → 400."""
    response = client.post(
        "/api/auth/verify/check-code",
        json={"code": "000000"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "invalide" in response.json()["detail"].lower()


def test_check_code_consumed_once(client, auth_headers):
    """Un code ne peut être utilisé qu'une seule fois → 400 la 2e fois."""
    # 1. Demander un code
    send_response = client.post(
        "/api/auth/verify/send-email",
        headers=auth_headers,
    )
    code = send_response.json()["debug_code"]

    # 2. Première utilisation (succès)
    r1 = client.post(
        "/api/auth/verify/check-code",
        json={"code": code},
        headers=auth_headers,
    )
    assert r1.status_code == 200

    # 3. Deuxième utilisation (échec, code consommé)
    r2 = client.post(
        "/api/auth/verify/check-code",
        json={"code": code},
        headers=auth_headers,
    )
    assert r2.status_code == 400
