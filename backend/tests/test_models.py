"""
Tests unitaires rapides pour les modèles SQLAlchemy.

L'objectif est de couvrir les méthodes `__repr__`, qui n'ont pas de logique
métier mais qui apparaissent dans la couverture de code.
"""
import uuid

from app.models import Camp, CampModality, ContactMessage, LandingPage, Registration, User
from app.models.enums import (
    CampStatus,
    ContactChannel,
    ModalityType,
    SeasonTheme,
    UserRole,
    UserStatus,
)


def test_user_repr():
    user = User(
        id=uuid.uuid4(),
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password_hash="hash",
        role=UserRole.SEM,
        status=UserStatus.ACTIVE,
    )
    assert "test@example.com" in repr(user)
    assert "sem" in repr(user)


def test_camp_repr():
    camp = Camp(id=uuid.uuid4(), name="Test Camp", slug="test-camp", organizer_id=uuid.uuid4())
    assert "test-camp" in repr(camp)


def test_camp_modality_repr():
    modality = CampModality(
        id=uuid.uuid4(),
        camp_id=uuid.uuid4(),
        type=ModalityType.AGE_RESTRICTION,
        label="12-17 ans",
    )
    assert "age_restriction" in repr(modality)
    assert "12-17 ans" in repr(modality)


def test_landing_page_repr():
    lp = LandingPage(
        id=uuid.uuid4(),
        camp_id=uuid.uuid4(),
        season_theme=SeasonTheme.ETE,
    )
    assert "ete" in repr(lp)


def test_registration_repr():
    reg = Registration(
        id=uuid.uuid4(),
        camp_id=uuid.uuid4(),
        first_name="Jean",
        last_name="Dupont",
        email="jean@example.com",
        confirmed=True,
    )
    assert "jean@example.com" in repr(reg)


def test_contact_message_repr():
    msg = ContactMessage(
        id=uuid.uuid4(),
        message="Hello",
        channel=ContactChannel.HOTLINE,
        email="contact@example.com",
    )
    assert "hotline" in repr(msg)
    assert "contact@example.com" in repr(msg)
