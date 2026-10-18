"""
Fixtures partagées pour tous les tests backend.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.db.base_class import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import User, UserRole, UserStatus

# Database dependency fallback
try:
    from app.db.session import get_db
except ImportError:
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

# Security fallbacks if security module does not exist yet
try:
    from app.core.security import create_access_token, hash_password
except ImportError:
    try:
        from app.security import create_access_token, hash_password
    except ImportError:
        def hash_password(password: str) -> str:
            return f"hashed_{password}"

        def create_access_token(subject: str) -> str:
            return f"fake_jwt_token_{subject}"


# ---------------------------------------------------------------------------
# Session de test avec rollback automatique
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    """Fournit une session SQLAlchemy réinitialisée à la fin du test."""
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(bind=connection)
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
# Utilisateur de test générique
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def test_user(db_session):
    """Crée un utilisateur de test générique."""
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        first_name="Admin",
        last_name="Test",
        email="admin@test.local",
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
    """Fournit les headers JWT d'authentification pour le user de test."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}