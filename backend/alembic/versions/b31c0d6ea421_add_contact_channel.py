"""add contact message channel

Revision ID: b31c0d6ea421
Revises: a5bf0dcf362e
Create Date: 2026-10-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b31c0d6ea421"
down_revision: Union[str, None] = "a5bf0dcf362e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    contact_channel = sa.Enum("HOTLINE", "CHATBOT", name="contactchannel")
    contact_channel.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "contact_messages",
        sa.Column(
            "channel",
            contact_channel,
            nullable=False,
            server_default="HOTLINE",
        ),
    )
    op.alter_column("contact_messages", "channel", server_default=None)


def downgrade() -> None:
    op.drop_column("contact_messages", "channel")
    sa.Enum(name="contactchannel").drop(op.get_bind(), checkfirst=True)