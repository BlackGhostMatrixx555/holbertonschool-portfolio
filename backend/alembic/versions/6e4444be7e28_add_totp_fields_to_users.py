"""add totp fields to users

Revision ID: 6e4444be7e28
Revises: c51e59a870dc
Create Date: 2026-10-22 21:24:18.217479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e4444be7e28'
down_revision: Union[str, None] = 'c51e59a870dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajout de totp_secret (nullable, pas de valeur par défaut nécessaire)
    op.add_column('users', sa.Column('totp_secret', sa.String(length=32), nullable=True))
    
    # Ajout de is_2fa_enabled avec une valeur par défaut FALSE
    # pour éviter l'erreur NotNullViolation sur les utilisateurs existants
    op.add_column(
        'users',
        sa.Column(
            'is_2fa_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_2fa_enabled')
    op.drop_column('users', 'totp_secret')
