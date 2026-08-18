"""Formalización individual de Disposición.

Revision ID: 20260818_0020
Revises: 20260813_0019
Create Date: 2026-08-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260818_0020"
down_revision: Union[str, Sequence[str], None] = "20260813_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "disposiciones",
        sa.Column("fecha_formalizacion", sa.Date(), nullable=True),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "usuario_registro_formalizacion",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "registrado_formalizacion_en",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_disposiciones_formalizacion_completa",
        "disposiciones",
        "(fecha_formalizacion IS NULL AND "
        "usuario_registro_formalizacion IS NULL AND "
        "registrado_formalizacion_en IS NULL) OR "
        "(fecha_formalizacion IS NOT NULL AND "
        "usuario_registro_formalizacion IS NOT NULL AND "
        "registrado_formalizacion_en IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_disposiciones_formalizacion_completa",
        "disposiciones",
        type_="check",
    )
    op.drop_column("disposiciones", "registrado_formalizacion_en")
    op.drop_column("disposiciones", "usuario_registro_formalizacion")
    op.drop_column("disposiciones", "fecha_formalizacion")
