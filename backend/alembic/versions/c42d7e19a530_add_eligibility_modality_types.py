"""add eligibility modality types

Revision ID: c42d7e19a530
Revises: b31c0d6ea421
Create Date: 2026-10-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c42d7e19a530"
down_revision: Union[str, None] = "b31c0d6ea421"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE modalitytype ADD VALUE IF NOT EXISTS 'AGE_RESTRICTION'")
    op.execute("ALTER TYPE modalitytype ADD VALUE IF NOT EXISTS 'EDUCATION_LEVEL'")
    op.execute("ALTER TYPE modalitytype ADD VALUE IF NOT EXISTS 'OTHER'")


def downgrade() -> None:
    pass