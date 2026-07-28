"""Crear tabla de decisiones administrativas.

Revision ID: 20260727_0007
Revises: 20260722_0006
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260727_0007"
down_revision: Union[str, Sequence[str], None] = "20260722_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "decisiones_administrativas",
        sa.Column(
            "id_decision",
            postgresql.UUID(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "solicitud_intervencion_id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "autoridad_decisora",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("fecha_decision", sa.Date(), nullable=False),
        sa.Column(
            "resultado",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("fundamento", sa.Text(), nullable=False),
        sa.Column(
            "fondo_interviniente",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "descripcion_fondo",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "usuario_registrante",
            sa.String(length=255),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id_decision",
            name="pk_decisiones_administrativas",
        ),
    )
    op.create_index(
        "ix_decisiones_administrativas_solicitud",
        "decisiones_administrativas",
        ["solicitud_intervencion_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_decisiones_administrativas_solicitud",
        table_name="decisiones_administrativas",
    )
    op.drop_table("decisiones_administrativas")
