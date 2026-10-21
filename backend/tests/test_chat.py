"""
Tests pour le chatbot et la hotline.
"""
import uuid
from app.models import ContactMessage, ContactChannel


def test_chatbot_reply(client):
    """POST /api/contact/chat renvoie une réponse et enregistre le message."""
    payload = {"message": "Quel est le prix du camp ?"}
    response = client.post("/api/contact/chat", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    assert "reply" in body
    assert "tarif" in body["reply"].lower() or "prix" in body["reply"].lower()
    assert body["channel"] == "chatbot"


def test_chatbot_saves_message_in_db(client, db_session):
    """Vérifie que le message est bien enregistré dans contact_messages."""
    payload = {"message": "Bonjour, quand commence le camp ?"}
    client.post("/api/contact/chat", json=payload)

    # Vérifier en base
    msg = db_session.query(ContactMessage).filter_by(channel=ContactChannel.CHATBOT).first()
    assert msg is not None
    assert msg.message == "Bonjour, quand commence le camp ?"


def test_hotline_message(client):
    """POST /api/contact/hotline enregistre un message."""
    payload = {
        "name": "Jean Dupont",
        "email": "jean@example.com",
        "message": "J'ai une question sur l'inscription."
    }
    response = client.post("/api/contact/hotline", json=payload)
    
    assert response.status_code == 201
    assert response.json()["status"] == "ok"


def test_hotline_saves_message_in_db(client, db_session):
    """Vérifie que le message de la hotline est bien enregistré."""
    payload = {
        "name": "Marie",
        "email": "marie@example.com",
        "message": "Problème d'inscription."
    }
    client.post("/api/contact/hotline", json=payload)

    msg = db_session.query(ContactMessage).filter_by(channel=ContactChannel.HOTLINE).first()
    assert msg is not None
    assert msg.name == "Marie"
    assert msg.channel == ContactChannel.HOTLINE
