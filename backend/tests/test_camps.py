"""
Tests pour les endpoints `/api/camps`.

Couvre :
- POST /api/camps            : création (succès, doublon slug, sans auth, user inexistant, dates inversées)
- GET  /api/camps            : liste (vide, avec données, filtre par statut)
- GET  /api/camps/{slug}/public : vue publique (succès, 404)
- PATCH /api/camps/{id}      : mise à jour (succès, dates invalides, 404, sans auth)
- DELETE /api/camps/{id}     : suppression (succès, 404, sans auth)
"""
from app.security import create_access_token


# ---------------------------------------------------------------------------
# POST /api/camps — création
# ---------------------------------------------------------------------------
def test_create_camp_success(client, auth_headers, test_user):
    """POST /api/camps avec données valides → 201 + camp créé."""
    payload = {
        "name": "Code Explorers — Été 2026",
        "description": "Un camp pour découvrir Python et le web.",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "city": "Paris",
        "age": 14,
        "capacity": 20,
        "status": "draft",
        "modalities": [
            {"type": "age_restriction", "label": "Avoir entre 12 et 17 ans"},
            {"type": "education_level", "label": "Niveau collège minimum"},
        ],
    }
    response = client.post("/api/camps", json=payload, headers=auth_headers)
    assert response.status_code == 201

    body = response.json()
    assert body["name"] == payload["name"]
    assert body["slug"] == "code-explorers-ete-2026"
    assert body["status"] == "draft"
    assert body["capacity"] == 20
    assert len(body["modalities"]) == 2
    assert body["organizer_id"] == str(test_user.id)


def test_create_camp_slug_uniqueness(client, auth_headers):
    """Deux camps avec le même nom → slugs différents (-2, -3, ...)."""
    payload = {
        "name": "Camp Dupliqué",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    r1 = client.post("/api/camps", json=payload, headers=auth_headers)
    r2 = client.post("/api/camps", json=payload, headers=auth_headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["slug"] == "camp-duplique"
    assert r2.json()["slug"] == "camp-duplique-2"


def test_create_camp_without_auth(client):
    """POST /api/camps sans token → 401."""
    payload = {
        "name": "Sans Auth",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    response = client.post("/api/camps", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Token d'authentification manquant."


def test_create_camp_with_unknown_user(client):
    """POST /api/camps avec un JWT valide pointant vers un user inexistant → 401."""
    # Token valide (signé), mais dont l'UUID n'existe pas en base.
    token = create_access_token(subject="11111111-1111-1111-1111-111111111111")
    payload = {
        "name": "UUID Bidon",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    response = client.post(
        "/api/camps",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Utilisateur introuvable."


def test_create_camp_with_invalid_token(client):
    """POST /api/camps avec un token bidon → 401."""
    payload = {
        "name": "Token Bidon",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    response = client.post(
        "/api/camps",
        json=payload,
        headers={"Authorization": "Bearer ceci-nest-pas-un-jwt"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token invalide ou expiré."


def test_create_camp_invalid_dates(client, auth_headers):
    """POST /api/camps avec end_date < start_date → 422."""
    payload = {
        "name": "Dates Inversées",
        "start_date": "2026-07-15",
        "end_date": "2026-07-01",
        "capacity": 10,
    }
    response = client.post("/api/camps", json=payload, headers=auth_headers)
    assert response.status_code == 422

    body = response.json()
    assert any(
        "end_date doit être supérieure ou égale à start_date" in err["msg"]
        for err in body["detail"]
    )


# ---------------------------------------------------------------------------
# GET /api/camps — liste
# ---------------------------------------------------------------------------
def test_list_camps_empty(client):
    """GET /api/camps sur une base vide → 200 + []."""
    response = client.get("/api/camps")
    assert response.status_code == 200
    assert response.json() == []


def test_list_camps_returns_created(client, auth_headers):
    """GET /api/camps retourne les camps créés."""
    payload = {
        "name": "Camp à Lister",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    client.post("/api/camps", json=payload, headers=auth_headers)

    response = client.get("/api/camps")
    assert response.status_code == 200
    camps = response.json()
    assert len(camps) == 1
    assert camps[0]["name"] == "Camp à Lister"


def test_list_camps_filter_by_status(client, auth_headers):
    """GET /api/camps?status=draft filtre par statut."""
    payload_draft = {
        "name": "Camp Draft",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
        "status": "draft",
    }
    payload_published = {
        "name": "Camp Publié",
        "start_date": "2026-08-01",
        "end_date": "2026-08-15",
        "capacity": 10,
        "status": "published",
    }
    client.post("/api/camps", json=payload_draft, headers=auth_headers)
    client.post("/api/camps", json=payload_published, headers=auth_headers)

    response = client.get("/api/camps?status=draft")
    assert response.status_code == 200
    camps = response.json()
    assert len(camps) == 1
    assert camps[0]["name"] == "Camp Draft"


# ---------------------------------------------------------------------------
# GET /api/camps/{slug}/public — vue publique
# ---------------------------------------------------------------------------
def test_get_public_camp_success(client, auth_headers):
    """GET /api/camps/{slug}/public → 200 + vue filtrée."""
    payload = {
        "name": "Camp Public",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 20,
        "modalities": [
            {"type": "age_restriction", "label": "12-17 ans"},
        ],
    }
    client.post("/api/camps", json=payload, headers=auth_headers)

    response = client.get("/api/camps/camp-public/public")
    assert response.status_code == 200

    body = response.json()
    assert body["name"] == "Camp Public"
    assert body["slug"] == "camp-public"
    assert len(body["modalities"]) == 1
    # Les champs internes ne sont PAS exposés
    assert "organizer_id" not in body
    assert "capacity" not in body


def test_get_public_camp_not_found(client):
    """GET /api/camps/{slug}/public avec slug inexistant → 404."""
    response = client.get("/api/camps/slug-inexistant/public")
    assert response.status_code == 404
    assert response.json()["detail"] == "Camp introuvable."


# ---------------------------------------------------------------------------
# PATCH /api/camps/{id} — mise à jour
# ---------------------------------------------------------------------------
def test_update_camp_success(client, auth_headers):
    """PATCH /api/camps/{id} → 200 + champs modifiés."""
    create_payload = {
        "name": "Camp à Modifier",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
        "status": "draft",
    }
    create_response = client.post("/api/camps", json=create_payload, headers=auth_headers)
    camp_id = create_response.json()["id"]

    update_payload = {"name": "Camp Modifié", "capacity": 25, "status": "published"}
    response = client.patch(f"/api/camps/{camp_id}", json=update_payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Camp Modifié"
    assert body["capacity"] == 25
    assert body["status"] == "published"
    # Le slug reste inchangé (volontairement)
    assert body["slug"] == "camp-a-modifier"


def test_update_camp_invalid_dates(client, auth_headers):
    """PATCH /api/camps/{id} avec dates inversées → 422."""
    create_payload = {
        "name": "Camp Test",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    create_response = client.post("/api/camps", json=create_payload, headers=auth_headers)
    camp_id = create_response.json()["id"]

    update_payload = {"start_date": "2026-08-01", "end_date": "2026-07-15"}
    response = client.patch(f"/api/camps/{camp_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 422


def test_update_camp_not_found(client, auth_headers):
    """PATCH /api/camps/{id} avec UUID inexistant → 404."""
    fake_id = "11111111-1111-1111-1111-111111111111"
    response = client.patch(
        f"/api/camps/{fake_id}",
        json={"name": "Nouveau Nom"},
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Camp introuvable."


def test_update_camp_without_auth(client):
    """PATCH /api/camps/{id} sans token → 401."""
    fake_id = "11111111-1111-1111-1111-111111111111"
    response = client.patch(f"/api/camps/{fake_id}", json={"name": "Nouveau Nom"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/camps/{id} — suppression
# ---------------------------------------------------------------------------
def test_delete_camp_success(client, auth_headers):
    """DELETE /api/camps/{id} → 204 + camp supprimé."""
    create_payload = {
        "name": "Camp à Supprimer",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    create_response = client.post("/api/camps", json=create_payload, headers=auth_headers)
    camp_id = create_response.json()["id"]

    response = client.delete(f"/api/camps/{camp_id}", headers=auth_headers)
    assert response.status_code == 204

    list_response = client.get("/api/camps")
    assert list_response.json() == []


def test_delete_camp_not_found(client, auth_headers):
    """DELETE /api/camps/{id} avec UUID inexistant → 404."""
    fake_id = "11111111-1111-1111-1111-111111111111"
    response = client.delete(f"/api/camps/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_delete_camp_without_auth(client):
    """DELETE /api/camps/{id} sans token → 401."""
    fake_id = "11111111-1111-1111-1111-111111111111"
    response = client.delete(f"/api/camps/{fake_id}")
    assert response.status_code == 401
