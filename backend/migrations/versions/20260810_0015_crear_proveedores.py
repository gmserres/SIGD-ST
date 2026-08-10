"""Crear Maestro de Proveedores.

Revision ID: 20260810_0015
Revises: 20260802_0014
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260810_0015"
down_revision: Union[str, Sequence[str], None] = "20260802_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "proveedores",
        sa.Column(
            "id_proveedor",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "cuit",
            sa.String(length=11),
            nullable=False,
        ),
        sa.Column(
            "razon_social",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id_proveedor",
            name="pk_proveedores",
        ),
        sa.UniqueConstraint(
            "cuit",
            name="uq_proveedores_cuit",
        ),
    )


def downgrade() -> None:
    op.drop_table("proveedores")
