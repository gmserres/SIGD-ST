"""Crear tabla de disposiciones emitidas.

Revision ID: 20260728_0008
Revises: 20260727_0007
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260728_0008"
down_revision: Union[str, Sequence[str], None] = "20260727_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disposiciones",
        sa.Column(
            "id_disposicion",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column("expediente_id", sa.String(32), nullable=False),
        sa.Column(
            "configuracion_uc_id",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "numero_disposicion",
            sa.String(255),
            nullable=False,
        ),
        sa.Column("fecha_emision", sa.DateTime(), nullable=False),
        sa.Column(
            "fondo_interviniente",
            sa.String(64),
            nullable=False,
        ),
        sa.Column("numero_op", sa.String(255), nullable=False),
        sa.Column(
            "numero_liquidacion",
            sa.String(255),
            nullable=True,
        ),
        sa.Column("proveedor", sa.String(255), nullable=False),
        sa.Column("cuit", sa.String(32), nullable=False),
        sa.Column("importe", sa.Numeric(18, 2), nullable=False),
        sa.Column("objeto", sa.Text(), nullable=False),
        sa.Column("establecimiento", sa.Text(), nullable=False),
        sa.Column(
            "valor_uc_aplicado",
            sa.Numeric(18, 6),
            nullable=False,
        ),
        sa.Column(
            "cantidad_uc",
            sa.Numeric(20, 8),
            nullable=False,
        ),
        sa.Column(
            "procedimiento_contratacion",
            sa.String(255),
            nullable=False,
        ),
        sa.Column("norma_uc", sa.Text(), nullable=False),
        sa.Column("texto_emitido", sa.Text(), nullable=False),
        sa.Column("ruta_docx", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["expediente_id"],
            ["expedientes.id"],
            name="fk_disposiciones_expediente",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["configuracion_uc_id"],
            ["configuraciones_uc.id_configuracion"],
            name="fk_disposiciones_configuracion_uc",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id_disposicion",
            name="pk_disposiciones",
        ),
        sa.UniqueConstraint(
            "expediente_id",
            name="uq_disposiciones_expediente",
        ),
        sa.UniqueConstraint(
            "numero_disposicion",
            name="uq_disposiciones_numero",
        ),
    )
    op.create_index(
        "ix_disposiciones_configuracion_uc",
        "disposiciones",
        ["configuracion_uc_id"],
    )
    op.create_index(
        "ix_disposiciones_fecha_emision",
        "disposiciones",
        ["fecha_emision"],
    )
    op.create_index(
        "ix_disposiciones_numero_op",
        "disposiciones",
        ["numero_op"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_disposiciones_numero_op",
        table_name="disposiciones",
    )
    op.drop_index(
        "ix_disposiciones_fecha_emision",
        table_name="disposiciones",
    )
    op.drop_index(
        "ix_disposiciones_configuracion_uc",
        table_name="disposiciones",
    )
    op.drop_table("disposiciones")
