"""
Tests du chatbot et de son stockage MongoDB.

MongoDB est remplacé par mongomock (base en mémoire) : les tests n'ont
pas besoin d'un serveur MongoDB et chaque test part d'une base vide.
"""
import uuid
from datetime import date

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from app.core.security import create_access_token, hash_password
from app.db.mongo import CONVERSATIONS, ensure_indexes, get_mongo_db
from app.main import app
from app.models import Camp, CampModality, CampStatus, ModalityType, User, UserRole, UserStatus
from app.services.chat_service import detect_intent


def _camp(db_session, organizer_id, status=CampStatus.PUBLISHED):
    camp = Camp(
        organizer_id=organizer_id,
        name="Chat Camp",
        slug=f"chat-camp-{uuid.uuid4().hex[:8]}",
        description="Python, web et robotique.",
        start_date=date(2026, 7, 6),
        end_date=date(2026, 7, 17),
        city="Lyon",
        min_age=12,
        max_age=15,
        capacity=24,
        status=status,
    )
    camp.modalities.append(CampModality(type=ModalityType.EDUCATION_LEVEL, label="Niveau collège"))
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp


def _chat(client, slug, message, session_id=None):
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    return client.post(f"/api/camps/{slug}/chat", json=payload)


# ---- Détection d'intention (tests unitaires, sans base) ----------------------

@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Bonjour !", "greeting"),
        ("Quand commence le camp ?", "dates"),
        ("Où se passe le camp ?", "location"),
        ("Il faut avoir quel âge ?", "age"),
        ("Reste-t-il des places ?", "places"),
        ("Comment je m'inscris ?", "registration"),
        ("Je veux parler à un humain", "human"),
        ("Qu'est-ce qu'on va apprendre ?", "program"),
        ("Le ciel est bleu", "unknown"),
        ("Merci beaucoup", "unknown"),  # "ou" dans "beaucoup" ne doit pas compter
    ],
)
def test_detect_intent(message, expected):
    assert detect_intent(message) == expected


# ---- Conversation publique ----------------------------------------------------

def test_chat_answers_with_real_camp_data(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)

    response = _chat(client, camp.slug, "Quand commence le camp ?")
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "dates"
    assert "06/07/2026" in body["reply"] and "17/07/2026" in body["reply"]
    assert body["session_id"]

    age = _chat(client, camp.slug, "Quel âge faut-il ?", body["session_id"]).json()
    assert "12 à 15 ans" in age["reply"] and "Niveau collège" in age["reply"]


def test_conversation_is_one_mongo_document(client, db_session, mongo_db, test_user):
    camp = _camp(db_session, test_user.id)
    first = _chat(client, camp.slug, "Bonjour").json()
    _chat(client, camp.slug, "Où est le camp ?", first["session_id"])

    documents = list(mongo_db[CONVERSATIONS].find({"camp_id": str(camp.id)}))
    assert len(documents) == 1  # même session -> même document
    conversation = documents[0]
    assert conversation["camp_slug"] == camp.slug
    assert [message["role"] for message in conversation["messages"]] == ["visitor", "bot", "visitor", "bot"]
    assert conversation["updated_at"] >= conversation["created_at"]


def test_chat_on_draft_camp_returns_404(client, db_session, test_user):
    camp = _camp(db_session, test_user.id, status=CampStatus.DRAFT)
    assert _chat(client, camp.slug, "Bonjour").status_code == 404


def test_chat_validates_message(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)
    assert _chat(client, camp.slug, "").status_code == 422
    assert _chat(client, camp.slug, "x" * 501).status_code == 422
    assert _chat(client, camp.slug, "Bonjour", session_id="bad id!").status_code == 422


def test_session_cannot_be_reused_on_another_camp(client, db_session, mongo_db, test_user):
    ensure_indexes(mongo_db)  # index unique sur session_id
    first_camp = _camp(db_session, test_user.id)
    second_camp = _camp(db_session, test_user.id)
    session_id = _chat(client, first_camp.slug, "Bonjour").json()["session_id"]
    assert _chat(client, second_camp.slug, "Bonjour", session_id).status_code == 409


def test_chat_returns_503_when_mongo_is_down(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)

    class DownCollection:
        def update_one(self, *args, **kwargs):
            raise ServerSelectionTimeoutError("MongoDB arrêté")

    app.dependency_overrides[get_mongo_db] = lambda: {CONVERSATIONS: DownCollection()}
    response = _chat(client, camp.slug, "Bonjour")
    assert response.status_code == 503


# ---- Espace organisateur : historique et statistiques ------------------------

def test_organizer_reads_conversations_and_stats(client, db_session, auth_headers, test_user):
    camp = _camp(db_session, test_user.id)
    session = _chat(client, camp.slug, "Quand commence le camp ?").json()["session_id"]
    _chat(client, camp.slug, "Et ça finit quand ?", session)
    _chat(client, camp.slug, "Où est le camp ?")  # 2e visiteur

    conversations = client.get(f"/api/camps/{camp.id}/chat/conversations", headers=auth_headers)
    assert conversations.status_code == 200
    assert len(conversations.json()) == 2

    stats = client.get(f"/api/camps/{camp.id}/chat/stats", headers=auth_headers).json()
    assert stats["conversations"] == 2
    assert stats["visitor_messages"] == 3
    assert stats["top_intents"][0] == {"intent": "dates", "count": 2}


def test_other_organizer_cannot_read_conversations(client, db_session, test_user):
    camp = _camp(db_session, test_user.id)
    other = User(
        email="other-chat@example.com",
        password_hash=hash_password("organizer-password"),
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    db_session.add(other)
    db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(subject=other.id)}"}
    assert client.get(f"/api/camps/{camp.id}/chat/stats", headers=headers).status_code == 403


def test_indexes_include_ttl_for_gdpr(mongo_db):
    ensure_indexes(mongo_db)
    indexes = mongo_db[CONVERSATIONS].index_information()
    assert indexes["updated_at_ttl"]["expireAfterSeconds"] == 90 * 24 * 3600
    assert indexes["session_id_1"]["unique"] is True
