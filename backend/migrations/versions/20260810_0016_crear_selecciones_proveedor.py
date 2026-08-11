"""Crear selecciones de Proveedor.

Revision ID: 20260810_0016
Revises: 20260810_0015
Create Date: 2026-08-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260810_0016"
down_revision: Union[str, Sequence[str], None] = "20260810_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "selecciones_proveedor",
        sa.Column("id_seleccion", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("solicitud_intervencion_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("decision_administrativa_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("proveedor_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("fecha_seleccion", sa.DateTime(), nullable=False),
        sa.Column("seleccionado_por", sa.String(length=255), nullable=False),
        sa.Column("proveedor_cuit", sa.String(length=11), nullable=False),
        sa.Column("proveedor_razon_social", sa.String(length=255), nullable=False),
        sa.Column("motivo_reemplazo", sa.Text(), nullable=True),
        sa.Column("vigente", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["solicitud_intervencion_id"],
            ["solicitudes_intervencion.id_solicitud"],
            name="fk_selecciones_proveedor_solicitud",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["decision_administrativa_id"],
            ["decisiones_administrativas.id_decision"],
            name="fk_selecciones_proveedor_decision",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["proveedor_id"],
            ["proveedores.id_proveedor"],
            name="fk_selecciones_proveedor_proveedor",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id_seleccion", name="pk_selecciones_proveedor"),
    )
    op.create_index("ix_selecciones_proveedor_solicitud", "selecciones_proveedor", ["solicitud_intervencion_id"], unique=False)
    op.create_index("ix_selecciones_proveedor_decision", "selecciones_proveedor", ["decision_administrativa_id"], unique=False)
    op.create_index("ix_selecciones_proveedor_proveedor", "selecciones_proveedor", ["proveedor_id"], unique=False)
    op.create_index("ix_selecciones_proveedor_fecha", "selecciones_proveedor", ["fecha_seleccion"], unique=False)
    op.create_index(
        "uq_selecciones_proveedor_solicitud_vigente",
        "selecciones_proveedor",
        ["solicitud_intervencion_id"],
        unique=True,
        postgresql_where=sa.text("vigente IS TRUE"),
    )


def downgrade() -> None:
    op.drop_index("uq_selecciones_proveedor_solicitud_vigente", table_name="selecciones_proveedor")
    op.drop_index("ix_selecciones_proveedor_fecha", table_name="selecciones_proveedor")
    op.drop_index("ix_selecciones_proveedor_proveedor", table_name="selecciones_proveedor")
    op.drop_index("ix_selecciones_proveedor_decision", table_name="selecciones_proveedor")
    op.drop_index("ix_selecciones_proveedor_solicitud", table_name="selecciones_proveedor")
    op.drop_table("selecciones_proveedor")
