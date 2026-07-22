"""Crear tabla operativa de expedientes.

Revision ID: 20260722_0004
Revises: 20260722_0003
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0004"
down_revision: Union[str, Sequence[str], None] = "20260722_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(sa.Sequence("expedientes_id_seq")))
    op.create_table(
        "expedientes",
        sa.Column("secuencia", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("numero_interno", sa.String(length=255), nullable=False),
        sa.Column("numero_gdeba", sa.String(length=255), nullable=True),
        sa.Column("solicitud_intervencion_id", sa.String(length=64), nullable=True),
        sa.Column("decision_administrativa_id", sa.String(length=64), nullable=True),
        sa.Column("id_suna", sa.String(length=255), nullable=True),
        sa.Column("tipo_tramite", sa.String(length=64), nullable=False),
        sa.Column("estado", sa.String(length=64), nullable=False),
        sa.Column("establecimiento", sa.Text(), nullable=True),
        sa.Column("objeto", sa.Text(), nullable=True),
        sa.Column("numero_disposicion", sa.String(length=255), nullable=True),
        sa.Column("creado", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("secuencia", name="pk_expedientes"),
        sa.UniqueConstraint("id", name="uq_expedientes_id"),
    )
    op.create_index("ix_expedientes_solicitud", "expedientes", ["solicitud_intervencion_id"])
    op.create_index("ix_expedientes_decision", "expedientes", ["decision_administrativa_id"])
    op.create_index("ix_expedientes_id_suna", "expedientes", ["id_suna"])
    op.create_index("ix_expedientes_estado", "expedientes", ["estado"])


def downgrade() -> None:
    op.drop_index("ix_expedientes_estado", table_name="expedientes")
    op.drop_index("ix_expedientes_id_suna", table_name="expedientes")
    op.drop_index("ix_expedientes_decision", table_name="expedientes")
    op.drop_index("ix_expedientes_solicitud", table_name="expedientes")
    op.drop_table("expedientes")
    op.execute(sa.schema.DropSequence(sa.Sequence("expedientes_id_seq")))
