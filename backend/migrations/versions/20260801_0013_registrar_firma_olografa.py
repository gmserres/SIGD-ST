"""Registrar firma ológrafa de disposiciones emitidas.

Revision ID: 20260801_0013
Revises: 20260729_0012
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260801_0013"
down_revision: Union[str, Sequence[str], None] = "20260729_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expedientes",
        sa.Column("fecha_firma", sa.Date(), nullable=True),
    )
    op.add_column(
        "expedientes",
        sa.Column(
            "usuario_registro_firma",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("expedientes", "usuario_registro_firma")
    op.drop_column("expedientes", "fecha_firma")
