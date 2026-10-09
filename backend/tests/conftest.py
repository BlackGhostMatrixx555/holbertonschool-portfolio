"""
Fixtures partagées pour tous les tests.

Stratégie de test (Option A) :
- On utilise la MÊME base PostgreSQL que le développement (via Docker).
- Chaque test tourne dans une transaction qui est **rollback** à la fin.
- Résultat : aucun test ne laisse de données derrière lui, et la base
  reste dans son état initial entre chaque test.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import User, UserRole, UserStatus
from app.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Session de test avec rollback automatique
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    """Fournit une session SQLAlchemy qui sera rollback à la fin du test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction_):
        if transaction_.nested and not transaction_.parent.nested:
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Fournit un TestClient FastAPI branché sur la session de test."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Utilisateur de test
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def test_user(db_session):
    """Crée un utilisateur de test (super_admin) dans la transaction courante."""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        first_name="Tété",
        last_name="Dufrénoy",
        email="tete@camporga.test",
        password_hash=hash_password("motdepasse123"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Fournit les headers d'authentification JWT pour le user de test.

    On génère un vrai JWT via `create_access_token`, comme le ferait
    l'endpoint `/api/auth/login`. Les tests n'ont pas besoin de savoir
    comment le token est fabriqué — ils l'utilisent tel quel.
    """
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
