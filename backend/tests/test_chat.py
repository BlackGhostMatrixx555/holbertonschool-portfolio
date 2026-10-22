"""
Tests pour le chatbot et la hotline.

Couvre :
- POST /api/contact/chat : réponse du bot, persistance du message, hotline.
- POST /api/contact/hotline : enregistrement du message.
"""
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
    payload = {"message": "Message unique de test 42"}
    client.post("/api/contact/chat", json=payload)

    # Vérifier en base en filtrant par le contenu exact du message
    msg = db_session.query(ContactMessage).filter_by(
        channel=ContactChannel.CHATBOT,
        message="Message unique de test 42"
    ).first()
    assert msg is not None
    assert msg.message == "Message unique de test 42"


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
