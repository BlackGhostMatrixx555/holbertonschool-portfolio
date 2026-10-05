"""
Tests pour la route `/health`.

Vérifie que le serveur démarre et répond correctement.
"""


def test_health_check(client):
    """`GET /health` doit retourner 200 + {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
