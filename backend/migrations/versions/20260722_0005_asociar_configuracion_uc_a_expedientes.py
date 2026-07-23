"""Asociar Configuración UC a expedientes.

Revision ID: 20260722_0005
Revises: 20260722_0004
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0005"
down_revision: Union[str, Sequence[str], None] = "20260722_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expedientes",
        sa.Column(
            "configuracion_uc_id",
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_expedientes_configuracion_uc",
        "expedientes",
        ["configuracion_uc_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_expedientes_configuracion_uc",
        "expedientes",
        "configuraciones_uc",
        ["configuracion_uc_id"],
        ["id_configuracion"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_expedientes_configuracion_uc",
        "expedientes",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_expedientes_configuracion_uc",
        table_name="expedientes",
    )
    op.drop_column("expedientes", "configuracion_uc_id")
