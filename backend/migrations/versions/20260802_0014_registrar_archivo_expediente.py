"""Registrar archivo institucional del expediente.

Revision ID: 20260802_0014
Revises: 20260801_0013
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260802_0014"
down_revision: Union[str, Sequence[str], None] = "20260801_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expedientes",
        sa.Column("fecha_archivo", sa.Date(), nullable=True),
    )
    op.add_column(
        "expedientes",
        sa.Column(
            "usuario_registro_archivo",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("expedientes", "usuario_registro_archivo")
    op.drop_column("expedientes", "fecha_archivo")
