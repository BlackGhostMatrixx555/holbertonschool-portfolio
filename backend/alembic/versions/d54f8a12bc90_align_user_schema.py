"""align user schema with current roles

Revision ID: d54f8a12bc90
Revises: c42d7e19a530
Create Date: 2026-10-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d54f8a12bc90"
down_revision: Union[str, None] = "c42d7e19a530"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SEM'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SWE'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SSM'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'DC'")
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'DISABLED'")
    op.alter_column("users", "first_name", nullable=True)
    op.alter_column("users", "last_name", nullable=True)


def downgrade() -> None:
    op.alter_column("users", "last_name", nullable=False)
    op.alter_column("users", "first_name", nullable=False)