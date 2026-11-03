"""
Tests des règles métier ajoutées lors de la restructuration :
profil connecté, détail d'un camp, places restantes, cohérence des âges
et de la capacité, accès du super admin, limites de longueur.
"""
import uuid
from datetime import date

from app.core.security import create_access_token, hash_password
from app.models import Camp, CampStatus, User, UserRole, UserStatus


def _organizer(db_session, email="orga@example.com"):
    user = User(
        email=email,
        password_hash=hash_password("organizer-password"),
        first_name="Orga",
        last_name="Nizer",
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _camp(db_session, organizer_id, capacity=3, status=CampStatus.PUBLISHED):
    camp = Camp(
        organizer_id=organizer_id,
        name="Rules Camp",
        slug=f"rules-camp-{uuid.uuid4().hex[:8]}",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 7),
        city="Lille",
        age=12,
        capacity=capacity,
        status=status,
    )
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp


def _register(client, slug, email):
    return client.post(
        f"/api/camps/{slug}/registrations",
        json={"first_name": "Grace", "last_name": "Hopper", "email": email},
    )


# ---- /auth/me ----------------------------------------------------------------

def test_me_returns_current_user_without_password(client, auth_headers, test_user):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == test_user.email
    assert body["role"] == "super_admin"
    assert "password_hash" not in body


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_login_is_case_insensitive_on_email(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"email": test_user.email.upper(), "password": "motdepasse123"},
    )
    assert response.status_code == 200


# ---- Détail d'un camp et places restantes ------------------------------------

def test_get_camp_detail_for_owner(client, db_session):
    organizer = _organizer(db_session)
    camp = _camp(db_session, organizer.id)
    response = client.get(f"/api/camps/{camp.id}", headers=_headers(organizer))
    assert response.status_code == 200
    assert response.json()["registrations_count"] == 0


def test_get_camp_detail_forbidden_for_other_organizer(client, db_session):
    owner = _organizer(db_session, "owner@example.com")
    other = _organizer(db_session, "other@example.com")
    camp = _camp(db_session, owner.id)
    response = client.get(f"/api/camps/{camp.id}", headers=_headers(other))
    assert response.status_code == 403


def test_public_camp_shows_remaining_places_but_not_capacity(client, db_session, test_user):
    camp = _camp(db_session, test_user.id, capacity=3)
    assert _register(client, camp.slug, "a@example.com").status_code == 201

    body = client.get(f"/api/camps/{camp.slug}/public").json()
    assert body["remaining_places"] == 2
    assert "capacity" not in body
    assert "organizer_id" not in body


def test_draft_camp_is_hidden_from_public_list(client, db_session, test_user):
    _camp(db_session, test_user.id, status=CampStatus.DRAFT)
    assert client.get("/api/public/camps").json() == []


# ---- Validation des données --------------------------------------------------

def test_create_camp_rejects_invalid_age(client, auth_headers):
    payload = {"name": "Ages", "start_date": "2026-07-01", "end_date": "2026-07-05", "capacity": 10, "age": 150}
    assert client.post("/api/camps", json=payload, headers=auth_headers).status_code == 422


def test_camp_without_age_is_open_to_all(client, auth_headers):
    payload = {"name": "Tous âges", "start_date": "2026-07-01", "end_date": "2026-07-05", "capacity": 10}
    body = client.post("/api/camps", json=payload, headers=auth_headers).json()
    assert body["age"] is None


def test_create_camp_rejects_zero_capacity(client, auth_headers):
    payload = {"name": "Zero", "start_date": "2026-07-01", "end_date": "2026-07-05", "capacity": 0}
    assert client.post("/api/camps", json=payload, headers=auth_headers).status_code == 422


def test_capacity_cannot_drop_below_registrations(client, db_session, auth_headers, test_user):
    camp = _camp(db_session, test_user.id, capacity=3)
    _register(client, camp.slug, "a@example.com")
    _register(client, camp.slug, "b@example.com")
    response = client.patch(f"/api/camps/{camp.id}", json={"capacity": 1}, headers=auth_headers)
    assert response.status_code == 422


def test_contact_message_too_long_is_rejected(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)
    response = client.post(
        f"/api/camps/{camp.slug}/contact-messages",
        json={"name": "Spam", "email": "spam@example.com", "message": "x" * 2001},
    )
    assert response.status_code == 422


def test_registration_email_is_normalised(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)
    assert _register(client, camp.slug, "Ada@Example.com").status_code == 201
    # Même adresse avec une autre casse : doublon détecté.
    assert _register(client, camp.slug, "ada@example.com").status_code == 409


# ---- Droits du super admin ---------------------------------------------------

def test_super_admin_can_list_registrations_of_any_camp(client, db_session, auth_headers):
    organizer = _organizer(db_session)
    camp = _camp(db_session, organizer.id)
    _register(client, camp.slug, "a@example.com")
    response = client.get(f"/api/camps/{camp.id}/registrations", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_republishing_keeps_first_publication_date(client, db_session, auth_headers, test_user):
    camp = _camp(db_session, test_user.id, status=CampStatus.DRAFT)
    payload = {"season_theme": "summer", "hero_title": "Hello", "publish": True}
    first = client.put(f"/api/camps/{camp.id}/landing-page", json=payload, headers=auth_headers).json()
    second = client.put(f"/api/camps/{camp.id}/landing-page", json=payload, headers=auth_headers).json()
    assert first["published_at"] == second["published_at"]


# ---- Administration des comptes ---------------------------------------------

def test_super_admin_changes_role_and_status(client, db_session, auth_headers):
    organizer = _organizer(db_session)
    role = client.patch(f"/api/users/{organizer.id}/role", json={"role": "swe"}, headers=auth_headers)
    assert role.status_code == 200 and role.json()["role"] == "swe"

    disabled = client.patch(f"/api/users/{organizer.id}/status", json={"status": "disabled"}, headers=auth_headers)
    assert disabled.status_code == 200
    # Un compte désactivé perd l'accès, même avec un jeton encore valide.
    assert client.get("/api/auth/me", headers=_headers(organizer)).status_code == 401


def test_super_admin_cannot_disable_own_account(client, auth_headers, test_user):
    response = client.patch(f"/api/users/{test_user.id}/status", json={"status": "disabled"}, headers=auth_headers)
    assert response.status_code == 409


def test_unknown_user_returns_404(client, auth_headers):
    response = client.patch(f"/api/users/{uuid.uuid4()}/role", json={"role": "swe"}, headers=auth_headers)
    assert response.status_code == 404


def test_duplicate_user_email_returns_409(client, auth_headers):
    payload = {"email": "twice@example.com", "password": "a-long-password", "first_name": "A", "last_name": "B"}
    assert client.post("/api/users", json=payload, headers=auth_headers).status_code == 201
    payload["email"] = "TWICE@example.com"  # même adresse, autre casse
    assert client.post("/api/users", json=payload, headers=auth_headers).status_code == 409
