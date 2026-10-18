import uuid
from datetime import date

from app.models import Camp, CampModality, ContactMessage, LandingPage, Registration, User
from app.models.user import UserRole, UserStatus
from app.models.camp import CampStatus
from app.models.landing_page import SeasonTheme
from app.models.contact_message import MessageStatus


def test_user_repr():
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hash",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    assert "test@example.com" in repr(user)


def test_camp_repr():
    camp = Camp(
        id=uuid.uuid4(),
        organizer_id=uuid.uuid4(),
        name="Summer Camp",
        slug="summer-camp",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 7),
        city="Example City",
        min_age=8,
        max_age=14,
        capacity=30,
        status=CampStatus.DRAFT,
    )
    assert "Summer Camp" in repr(camp)


def test_camp_modality_repr():
    modality = CampModality(id=uuid.uuid4())
    assert repr(modality) is not None


def test_contact_message_repr():
    message = ContactMessage(
        id=uuid.uuid4(),
        camp_id=uuid.uuid4(),
        name="John Doe",
        email="john@example.com",
        message="Hello world",
        status=MessageStatus.UNREAD,
    )
    assert "john@example.com" in repr(message)


def test_landing_page_repr():
    landing_page = LandingPage(
        id=uuid.uuid4(),
        camp_id=uuid.uuid4(),
        season_theme=SeasonTheme.SUMMER,
        hero_title="Welcome",
    )
    assert repr(landing_page) is not None


def test_registration_repr():
    registration = Registration(id=uuid.uuid4())
    assert repr(registration) is not None