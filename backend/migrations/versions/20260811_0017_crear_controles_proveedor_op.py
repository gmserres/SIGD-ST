"""Crear controles históricos Proveedor-OP.

Revision ID: 20260811_0017
Revises: 20260810_0016
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_0017"
down_revision: Union[str, Sequence[str], None] = "20260810_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SECUENCIA = sa.Sequence("controles_proveedor_op_secuencia_seq")


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(SECUENCIA))
    op.create_table(
        "controles_proveedor_op",
        sa.Column("id_control", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column(
            "secuencia",
            sa.Integer(),
            server_default=SECUENCIA.next_value(),
            nullable=False,
        ),
        sa.Column("expediente_id", sa.String(32), nullable=False),
        sa.Column("documento_secuencia", sa.Integer(), nullable=False),
        sa.Column(
            "solicitud_intervencion_id",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column(
            "seleccion_proveedor_id",
            sa.Uuid(as_uuid=False),
            nullable=False,
        ),
        sa.Column("estado", sa.String(64), nullable=False),
        sa.Column(
            "proveedor_cuit_seleccionado",
            sa.String(11),
            nullable=False,
        ),
        sa.Column(
            "proveedor_razon_social_seleccionada",
            sa.String(255),
            nullable=False,
        ),
        sa.Column("cuit_detectado", sa.String(11), nullable=True),
        sa.Column("razon_social_detectada", sa.Text(), nullable=True),
        sa.Column("advertencias", sa.JSON(), nullable=False),
        sa.Column("fecha_control", sa.DateTime(), nullable=False),
        sa.Column("modo_analisis", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "estado IN "
            "('COINCIDE', 'CUIT_DIFERENTE', 'NO_VERIFICABLE')",
            name="ck_controles_proveedor_op_estado",
        ),
        sa.ForeignKeyConstraint(
            ["expediente_id"],
            ["expedientes.id"],
            name="fk_controles_proveedor_op_expediente",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["documento_secuencia"],
            ["documentos.secuencia"],
            name="fk_controles_proveedor_op_documento",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_intervencion_id"],
            ["solicitudes_intervencion.id_solicitud"],
            name="fk_controles_proveedor_op_solicitud",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seleccion_proveedor_id"],
            ["selecciones_proveedor.id_seleccion"],
            name="fk_controles_proveedor_op_seleccion",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id_control", name="pk_controles_proveedor_op"
        ),
        sa.UniqueConstraint(
            "secuencia", name="uq_controles_proveedor_op_secuencia"
        ),
    )
    op.create_index(
        "ix_controles_proveedor_op_documento_secuencia",
        "controles_proveedor_op",
        ["documento_secuencia", "secuencia"],
        unique=False,
    )
    op.create_index(
        "ix_controles_proveedor_op_seleccion",
        "controles_proveedor_op",
        ["seleccion_proveedor_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_controles_proveedor_op_seleccion",
        table_name="controles_proveedor_op",
    )
    op.drop_index(
        "ix_controles_proveedor_op_documento_secuencia",
        table_name="controles_proveedor_op",
    )
    op.drop_table("controles_proveedor_op")
    op.execute(sa.schema.DropSequence(SECUENCIA))
