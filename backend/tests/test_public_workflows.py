import uuid
from datetime import date

from app.core.security import create_access_token
from app.models import Camp, CampStatus


def _camp(db_session, organizer_id, status=CampStatus.DRAFT):
    camp = Camp(
        organizer_id=organizer_id,
        name="Public Workflow Camp",
        slug=f"public-workflow-{uuid.uuid4().hex[:8]}",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 7),
        city="Paris",
        min_age=12,
        max_age=17,
        capacity=5,
        status=status,
    )
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp


def test_publish_landing_page_exposes_public_camp(client, db_session, auth_headers, test_user):
    camp = _camp(db_session, test_user.id)
    response = client.put(
        f"/api/camps/{camp.id}/landing-page",
        headers=auth_headers,
        json={
            "season_theme": "summer",
            "hero_title": "Build something brilliant",
            "hero_description": "A week of coding and collaboration.",
            "publish": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["hero_title"] == "Build something brilliant"

    public_response = client.get(f"/api/camps/{camp.slug}/public")
    assert public_response.status_code == 200
    assert public_response.json()["landing_page"]["hero_title"] == "Build something brilliant"
    assert "capacity" not in public_response.json()


def test_public_contact_message_and_owner_triage(client, db_session, auth_headers, test_user):
    camp = _camp(db_session, test_user.id, status=CampStatus.PUBLISHED)
    created = client.post(
        f"/api/camps/{camp.slug}/contact-messages",
        json={
            "name": "Alex Visitor",
            "email": "alex@example.com",
            "message": "Can I ask about accessibility?",
            "channel": "hotline",
        },
    )
    assert created.status_code == 201
    message_id = created.json()["id"]

    listing = client.get(
        f"/api/camps/{camp.id}/contact-messages",
        headers=auth_headers,
    )
    assert listing.status_code == 200
    assert listing.json()[0]["channel"] == "hotline"

    updated = client.patch(
        f"/api/contact-messages/{message_id}",
        headers=auth_headers,
        json={"status": "read"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "read"


def test_contact_message_is_rejected_for_draft_camp(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)
    response = client.post(
        f"/api/camps/{camp.slug}/contact-messages",
        json={"name": "Alex", "email": "alex@example.com", "message": "Hello"},
    )
    assert response.status_code == 404


def test_organizer_cannot_manage_another_organizers_camp(client, db_session):
    from app.models import User, UserRole, UserStatus

    acting_user = User(
        email="acting-organizer@example.com",
        password_hash="not-used-in-this-test",
        role=UserRole.ORGANIZER,
        status=UserStatus.ACTIVE,
    )
    other_user = User(
        email="other-organizer@example.com",
        password_hash="not-used-in-this-test",
        role=UserRole.ORGANIZER,
        status=UserStatus.ACTIVE,
    )
    db_session.add_all([acting_user, other_user])
    db_session.commit()
    camp = _camp(db_session, other_user.id)
    auth_headers = {
        "Authorization": f"Bearer {create_access_token(subject=str(acting_user.id))}"
    }

    update_response = client.patch(
        f"/api/camps/{camp.id}",
        headers=auth_headers,
        json={"name": "Unauthorized edit"},
    )
    list_response = client.get("/api/camps", headers=auth_headers)

    assert update_response.status_code == 403
    assert list_response.status_code == 200
    assert all(item["id"] != str(camp.id) for item in list_response.json())