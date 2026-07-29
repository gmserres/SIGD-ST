"""Crear tabla de checklists físicos.

Revision ID: 20260729_0010
Revises: 20260729_0009
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260729_0010"
down_revision: Union[str, Sequence[str], None] = "20260729_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checklists_fisicos",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("expediente_id", sa.String(32), nullable=False),
        sa.Column("factura", sa.Boolean(), nullable=False),
        sa.Column(
            "remito_conformidad",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column("cae", sa.Boolean(), nullable=False),
        sa.Column("arca", sa.Boolean(), nullable=False),
        sa.Column("arba", sa.Boolean(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("usuario", sa.String(255), nullable=False),
        sa.Column("fecha_registro", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["expediente_id"],
            ["expedientes.id"],
            name="fk_checklists_fisicos_expediente",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_checklists_fisicos",
        ),
        sa.UniqueConstraint(
            "expediente_id",
            name="uq_checklists_fisicos_expediente",
        ),
    )


def downgrade() -> None:
    op.drop_table("checklists_fisicos")
