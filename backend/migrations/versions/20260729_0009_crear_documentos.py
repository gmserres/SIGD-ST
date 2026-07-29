"""Crear tabla de documentos de expedientes.

Revision ID: 20260729_0009
Revises: 20260728_0008
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260729_0009"
down_revision: Union[str, Sequence[str], None] = "20260728_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documentos",
        sa.Column(
            "secuencia",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("expediente_id", sa.String(32), nullable=False),
        sa.Column("tipo", sa.String(64), nullable=False),
        sa.Column("nombre_archivo", sa.Text(), nullable=False),
        sa.Column("ruta", sa.Text(), nullable=False),
        sa.Column("fecha_carga", sa.DateTime(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("tamano_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["expediente_id"],
            ["expedientes.id"],
            name="fk_documentos_expediente",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "secuencia",
            name="pk_documentos",
        ),
    )
    op.create_index(
        "ix_documentos_expediente_fecha",
        "documentos",
        ["expediente_id", "fecha_carga", "secuencia"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_documentos_expediente_fecha",
        table_name="documentos",
    )
    op.drop_table("documentos")
