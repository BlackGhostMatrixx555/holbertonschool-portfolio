import uuid
from datetime import date

from app.models import Camp, CampStatus


def _published_camp(db_session, organizer_id, capacity=2):
    camp = Camp(
        organizer_id=organizer_id,
        name="Registration Camp",
        slug=f"registration-camp-{uuid.uuid4().hex[:8]}",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 7),
        city="Paris",
        min_age=12,
        max_age=17,
        capacity=capacity,
        status=CampStatus.PUBLISHED,
    )
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp


def test_public_registration_and_owner_confirmation(client, db_session, auth_headers, test_user):
    camp = _published_camp(db_session, test_user.id)
    response = client.post(
        f"/api/camps/{camp.slug}/registrations",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "comment": "Vegetarian meal, please.",
        },
    )

    assert response.status_code == 201
    registration = response.json()
    assert registration["confirmed"] is False

    listing = client.get(
        f"/api/camps/{camp.id}/registrations",
        headers=auth_headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    confirmation = client.patch(
        f"/api/registrations/{registration['id']}/attendance",
        json={"confirmed": True},
        headers=auth_headers,
    )
    assert confirmation.status_code == 200
    assert confirmation.json()["confirmed"] is True


def test_registration_rejects_duplicate_email(client, db_session, test_user):
    camp = _published_camp(db_session, test_user.id)
    payload = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}

    first = client.post(f"/api/camps/{camp.slug}/registrations", json=payload)
    duplicate = client.post(f"/api/camps/{camp.slug}/registrations", json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_registration_rejects_full_camp(client, db_session, test_user):
    camp = _published_camp(db_session, test_user.id, capacity=1)
    payload = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
    assert client.post(f"/api/camps/{camp.slug}/registrations", json=payload).status_code == 201

    response = client.post(
        f"/api/camps/{camp.slug}/registrations",
        json={**payload, "email": "grace@example.com"},
    )
    assert response.status_code == 409


def test_dashboard_summarizes_owned_camps_and_registrations(
    client, db_session, auth_headers, test_user
):
    camp = _published_camp(db_session, test_user.id)
    registration_response = client.post(
        f"/api/camps/{camp.slug}/registrations",
        json={"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
    )
    assert registration_response.status_code == 201

    response = client.get("/api/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["camps"]["published"] == 1
    assert response.json()["registrations"]["total"] == 1
    assert response.json()["recent_registrations"][0]["email"] == "ada@example.com"