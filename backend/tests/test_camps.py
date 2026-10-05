"""
Tests pour les endpoints `/api/camps`.

Couvre les 7 cas validés manuellement via Swagger :
- POST créer un camp (201)
- GET lister les camps (200)
- GET public par slug (200, filtré)
- POST sans header X-User-Id (401)
- POST avec UUID inexistant (401)
- POST avec dates inversées (422)
- POST avec dates valides (201)
"""


# ---------------------------------------------------------------------------
# POST /api/camps — création
# ---------------------------------------------------------------------------
def test_create_camp_success(client, auth_headers):
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
    assert body["organizer_id"] == auth_headers["X-User-Id"]


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
    """POST /api/camps sans header X-User-Id → 401."""
    payload = {
        "name": "Sans Auth",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    response = client.post("/api/camps", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Header X-User-Id manquant."


def test_create_camp_with_unknown_user(client):
    """POST /api/camps avec UUID inexistant → 401."""
    payload = {
        "name": "UUID Bidon",
        "start_date": "2026-07-01",
        "end_date": "2026-07-15",
        "capacity": 10,
    }
    headers = {"X-User-Id": "11111111-1111-1111-1111-111111111111"}
    response = client.post("/api/camps", json=payload, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Utilisateur introuvable."


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
    # Vérifie que le message d'erreur mentionne le problème de dates
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
    # Les champs publics sont présents
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
