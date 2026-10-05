"""
Fixtures partagées pour tous les tests.

Stratégie de test (Option A) :
- On utilise la MÊME base PostgreSQL que le développement (via Docker).
- Chaque test tourne dans une transaction qui est **rollback** à la fin.
- Résultat : aucun test ne laisse de données derrière lui, et la base
  reste dans son état initial entre chaque test.

Pourquoi pas une base de test séparée ? Pour la deadline serrée du MVP.
On pourra migrer vers une base `camporga_test` dédiée plus tard si besoin.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import User, UserRole, UserStatus


# ---------------------------------------------------------------------------
# Session de test avec rollback automatique
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    """Fournit une session SQLAlchemy qui sera rollback à la fin du test.

    Astuce : on ouvre une connexion, on démarre une transaction, et on
    "lie" la session à cette connexion. À la fin du test, on rollback la
    transaction — donc tout ce qui a été fait est annulé, même les commits.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    # Empêche SQLAlchemy de committer pour de vrai : les `session.commit()`
    # dans le code appelé (services, routes) deviennent des `flush()` dans
    # la transaction englobante.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction_):
        """Quand une transaction imbriquée se termine, on en démarre une
        nouvelle, pour que les `commit()` du code applicatif restent
        capturés par la transaction externe."""
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
    """Fournit un TestClient FastAPI branché sur la session de test.

    On remplace la dépendance `get_db` de FastAPI par notre session de
    test : comme ça, les routes utilisent la même transaction que nos
    fixtures, et tout est rollback à la fin.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Le rollback est géré par la fixture `db_session`.

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Utilisateur de test
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def test_user(db_session):
    """Crée un utilisateur de test (super_admin) dans la transaction courante.

    Comme tout est rollback à la fin du test, cet utilisateur n'existera
    jamais vraiment dans la base.
    """
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        first_name="Tété",
        last_name="Dufrénoy",
        email="tete@camporga.test",
        password_hash="fake-hash-for-now",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Fournit les headers d'authentification pour le stub actuel.

    Le stub `get_current_user` lit le header `X-User-Id` et charge
    l'utilisateur en base. Cette fixture renvoie le header prêt à l'emploi.
    """
    return {"X-User-Id": str(test_user.id)}
