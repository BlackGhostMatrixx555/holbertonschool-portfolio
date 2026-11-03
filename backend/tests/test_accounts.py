"""
Tests des fonctionnalités de comptes reprises de tete-work, dans la version fusionnée :
inscription, profil, suppression de compte, double authentification (TOTP),
vérification email / SMS, et garde-fous du super admin.
"""
import uuid
from datetime import date

import pyotp
import pytest

from app.core.security import create_access_token, create_two_factor_token, hash_password
from app.models import Camp, User, UserRole, UserStatus

PASSWORD = "un-mot-de-passe-solide"


def _user(db_session, email="orga@example.com", status=UserStatus.ACTIVE, role=UserRole.SEM, **extra):
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        first_name="Ada",
        last_name="Lovelace",
        role=role,
        status=status,
        **extra,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---- Inscription publique ------------------------------------------------------

def test_register_creates_pending_sem_account(client):
    response = client.post(
        "/api/auth/register",
        json={"first_name": "Grace", "last_name": "Hopper", "email": "Grace@Example.com", "password": PASSWORD},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "grace@example.com"
    assert body["role"] == "sem" and body["status"] == "inactive"
    assert "password_hash" not in body


def test_pending_account_cannot_log_in_until_activated(client, auth_headers):
    created = client.post(
        "/api/auth/register",
        json={"first_name": "Grace", "last_name": "Hopper", "email": "grace@example.com", "password": PASSWORD},
    ).json()

    pending = _login(client, "grace@example.com")
    assert pending.status_code == 403
    assert "attente de validation" in pending.json()["detail"]

    client.patch(f"/api/users/{created['id']}/status", json={"status": "active"}, headers=auth_headers)
    assert _login(client, "grace@example.com").json()["access_token"]


def test_pending_status_is_not_revealed_with_a_wrong_password(client, db_session):
    _user(db_session, email="pending@example.com", status=UserStatus.INACTIVE)
    assert _login(client, "pending@example.com", "mauvais-mot-de-passe").status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"first_name": "A", "last_name": "B", "email": "a@example.com", "password": "trop-court"},
        {"first_name": "A", "last_name": "B", "email": "pas-un-email", "password": PASSWORD},
        {"first_name": "", "last_name": "B", "email": "a@example.com", "password": PASSWORD},
        {"first_name": "A", "last_name": "B", "email": "a@example.com", "password": PASSWORD, "phone_number": "abc"},
    ],
)
def test_register_validates_input(client, payload):
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_register_duplicate_email_returns_409(client, db_session):
    _user(db_session, email="taken@example.com")
    payload = {"first_name": "A", "last_name": "B", "email": "TAKEN@example.com", "password": PASSWORD}
    assert client.post("/api/auth/register", json=payload).status_code == 409


# ---- Profil et suppression de compte -------------------------------------------

def test_user_updates_own_profile(client, db_session):
    user = _user(db_session)
    response = client.patch("/api/users/me", json={"phone_number": "+33 6 12 34 56 78"}, headers=_headers(user))
    assert response.status_code == 200
    assert response.json()["phone_number"] == "+33 6 12 34 56 78"
    assert response.json()["role"] == "sem"  # le profil ne permet pas de changer de rôle


def test_profile_update_ignores_role_field(client, db_session):
    user = _user(db_session)
    client.patch("/api/users/me", json={"role": "super_admin"}, headers=_headers(user))
    db_session.refresh(user)
    assert user.role == UserRole.SEM


def test_user_deletes_own_account(client, db_session):
    user = _user(db_session)
    headers = _headers(user)
    assert client.delete("/api/users/me", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_super_admin_cannot_delete_own_account(client, auth_headers):
    assert client.delete("/api/users/me", headers=auth_headers).status_code == 403


def test_account_with_camps_cannot_be_deleted(client, db_session, auth_headers):
    user = _user(db_session)
    db_session.add(
        Camp(
            organizer_id=user.id, name="Camp", slug=f"camp-{uuid.uuid4().hex[:6]}",
            start_date=date(2026, 7, 1), end_date=date(2026, 7, 5), city="Paris", capacity=5,
        )
    )
    db_session.commit()
    assert client.delete("/api/users/me", headers=_headers(user)).status_code == 409
    assert client.delete(f"/api/users/{user.id}", headers=auth_headers).status_code == 409


def test_super_admin_deletes_another_account(client, db_session, auth_headers):
    user = _user(db_session)
    assert client.delete(f"/api/users/{user.id}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/users/{user.id}", headers=auth_headers).status_code == 404


def test_organizer_cannot_delete_other_accounts(client, db_session, test_user):
    user = _user(db_session)
    assert client.delete(f"/api/users/{test_user.id}", headers=_headers(user)).status_code == 403


def test_super_admin_cannot_demote_himself(client, auth_headers, test_user):
    response = client.patch(f"/api/users/{test_user.id}/role", json={"role": "sem"}, headers=auth_headers)
    assert response.status_code == 409


def test_directeur_technique_role_exists(client, db_session, auth_headers):
    user = _user(db_session)
    response = client.patch(f"/api/users/{user.id}/role", json={"role": "dt"}, headers=auth_headers)
    assert response.json()["role"] == "dt"


# ---- Double authentification -----------------------------------------------------

def _enable_2fa(client, user):
    headers = _headers(user)
    setup = client.post("/api/auth/2fa/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    assert setup.json()["qr_code_base64"].startswith("data:image/png;base64,")
    enabled = client.post("/api/auth/2fa/enable", json={"code": pyotp.TOTP(secret).now()}, headers=headers)
    assert enabled.status_code == 200
    return secret


def test_full_two_factor_login(client, db_session):
    user = _user(db_session)
    secret = _enable_2fa(client, user)

    step1 = _login(client, user.email).json()
    assert step1["requires_2fa"] is True and step1["access_token"] is None

    step2 = client.post("/api/auth/2fa/login", json={"temp_token": step1["temp_token"], "code": pyotp.TOTP(secret).now()})
    assert step2.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {step2.json()['access_token']}"})
    assert me.json()["is_2fa_enabled"] is True


def test_temp_token_cannot_be_used_as_session_token(client, db_session):
    """Faille corrigée : le jeton temporaire ne doit ouvrir aucune route protégée."""
    user = _user(db_session)
    _enable_2fa(client, user)
    temp_token = _login(client, user.email).json()["temp_token"]
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {temp_token}"}).status_code == 401


def test_session_token_cannot_replace_temp_token(client, db_session):
    user = _user(db_session)
    secret = _enable_2fa(client, user)
    response = client.post(
        "/api/auth/2fa/login",
        json={"temp_token": create_access_token(subject=user.id), "code": pyotp.TOTP(secret).now()},
    )
    assert response.status_code == 401


def test_two_factor_login_rejects_wrong_code(client, db_session):
    user = _user(db_session)
    _enable_2fa(client, user)
    temp_token = _login(client, user.email).json()["temp_token"]
    assert client.post("/api/auth/2fa/login", json={"temp_token": temp_token, "code": "000000"}).status_code == 401


def test_enable_rejects_wrong_code(client, db_session):
    user = _user(db_session)
    headers = _headers(user)
    client.post("/api/auth/2fa/setup", headers=headers)
    assert client.post("/api/auth/2fa/enable", json={"code": "000000"}, headers=headers).status_code == 422


def test_setup_cannot_overwrite_active_2fa(client, db_session):
    """Faille corrigée : un nouveau setup écrasait le secret d'une 2FA active."""
    user = _user(db_session)
    _enable_2fa(client, user)
    assert client.post("/api/auth/2fa/setup", headers=_headers(user)).status_code == 409


def test_disable_requires_a_valid_code(client, db_session):
    """Faille corrigée : la désactivation ne demandait aucun code."""
    user = _user(db_session)
    secret = _enable_2fa(client, user)
    headers = _headers(user)
    assert client.post("/api/auth/2fa/disable", json={"code": "000000"}, headers=headers).status_code == 422
    assert client.post("/api/auth/2fa/disable", json={"code": pyotp.TOTP(secret).now()}, headers=headers).status_code == 200
    assert _login(client, user.email).json()["access_token"]


def test_two_factor_codes_must_be_six_digits(client, db_session):
    user = _user(db_session)
    assert client.post("/api/auth/2fa/enable", json={"code": "12ab56"}, headers=_headers(user)).status_code == 422


def test_expired_or_forged_temp_token_is_rejected(client, db_session):
    user = _user(db_session)
    _enable_2fa(client, user)
    forged = create_two_factor_token(uuid.uuid4())  # utilisateur inexistant
    assert client.post("/api/auth/2fa/login", json={"temp_token": forged, "code": "123456"}).status_code == 401
    assert client.post("/api/auth/2fa/login", json={"temp_token": "pas-un-jwt", "code": "123456"}).status_code == 401


# ---- Vérification email / SMS (codes stockés dans MongoDB) -----------------------

def test_email_code_round_trip(client, db_session, mongo_db):
    user = _user(db_session)
    headers = _headers(user)
    sent = client.post("/api/auth/verify/send-email", headers=headers).json()
    code = sent["debug_code"]  # renvoyé car ENVIRONMENT=development dans les tests

    stored = mongo_db["verification_codes"].find_one({"user_id": str(user.id)})
    assert stored["code_hash"] != code  # seule l'empreinte est stockée

    assert client.post("/api/auth/verify/check-code", json={"code": code}, headers=headers).status_code == 200
    # Un code ne sert qu'une fois.
    assert client.post("/api/auth/verify/check-code", json={"code": code}, headers=headers).status_code == 422


def test_sms_requires_a_phone_number(client, db_session):
    user = _user(db_session)
    assert client.post("/api/auth/verify/send-sms", headers=_headers(user)).status_code == 422


def test_sms_code_is_sent_when_phone_exists(client, db_session):
    user = _user(db_session, phone_number="+33612345678")
    response = client.post("/api/auth/verify/send-sms", headers=_headers(user))
    assert response.status_code == 200 and response.json()["message"] == "Code envoyé par SMS."


def test_code_is_blocked_after_too_many_attempts(client, db_session):
    user = _user(db_session)
    headers = _headers(user)
    code = client.post("/api/auth/verify/send-email", headers=headers).json()["debug_code"]
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        client.post("/api/auth/verify/check-code", json={"code": wrong}, headers=headers)
    # Même le bon code est refusé après 5 essais : il faut en redemander un.
    assert client.post("/api/auth/verify/check-code", json={"code": code}, headers=headers).status_code == 422


def test_debug_code_is_hidden_outside_development(client, db_session, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    user = _user(db_session)
    assert client.post("/api/auth/verify/send-email", headers=_headers(user)).json()["debug_code"] is None


def test_verification_requires_authentication(client):
    assert client.post("/api/auth/verify/send-email").status_code == 401
