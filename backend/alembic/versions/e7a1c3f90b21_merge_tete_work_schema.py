"""merge tete-work schema: single age, 2FA, phone, backups history

Fusion des deux versions du projet (collins + tete-work) :
- camps : min_age / max_age remplacés par une seule colonne `age` (âge minimum) ;
  les données existantes sont converties, rien n'est perdu sans raison.
- users : téléphone (vérification SMS) et champs de double authentification.
- userrole : ajout du rôle DT (directeur technique).
- backups : nouvelle table d'historique des exports.
Le module de paiement de tete-work n'est volontairement pas repris
(hors périmètre du MVP dans le cahier des charges).

Revision ID: e7a1c3f90b21
Revises: d54f8a12bc90
Create Date: 2026-11-03 16:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e7a1c3f90b21"
down_revision: Union[str, None] = "d54f8a12bc90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

backup_format = postgresql.ENUM("SQL", "CSV", name="backupformat", create_type=False)


def upgrade() -> None:
    # --- Rôle "directeur technique" -----------------------------------------
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'DT'")

    # --- Camps : une seule colonne age --------------------------------------
    op.add_column("camps", sa.Column("age", sa.SmallInteger(), nullable=True))
    # Conversion des données : on garde l'âge minimum ; "0 à 0" signifiait
    # "tous âges", ce qui devient NULL.
    op.execute(
        "UPDATE camps SET age = CASE WHEN min_age = 0 AND max_age = 0 THEN NULL ELSE min_age END"
    )
    op.drop_column("camps", "min_age")
    op.drop_column("camps", "max_age")

    # --- Users : téléphone et 2FA --------------------------------------------
    op.add_column("users", sa.Column("phone_number", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("totp_secret", sa.String(length=32), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_2fa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # --- Historique des sauvegardes ------------------------------------------
    backup_format.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "backups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("format", backup_format, nullable=False),
        sa.Column("triggered_by", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_kb", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["triggered_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backups_triggered_by"), "backups", ["triggered_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_backups_triggered_by"), table_name="backups")
    op.drop_table("backups")
    backup_format.drop(op.get_bind(), checkfirst=True)

    op.drop_column("users", "is_2fa_enabled")
    op.drop_column("users", "totp_secret")
    op.drop_column("users", "phone_number")

    # Retour à min_age / max_age : on recopie age dans les deux colonnes.
    op.add_column("camps", sa.Column("min_age", sa.SmallInteger(), nullable=True))
    op.add_column("camps", sa.Column("max_age", sa.SmallInteger(), nullable=True))
    op.execute("UPDATE camps SET min_age = COALESCE(age, 0), max_age = COALESCE(age, 0)")
    op.alter_column("camps", "min_age", nullable=False)
    op.alter_column("camps", "max_age", nullable=False)
    op.drop_column("camps", "age")
    # Une valeur ajoutée à un type ENUM PostgreSQL ne peut pas être retirée : DT reste.
