"""Crear validaciones administrativas y sus controles snapshot.

Revision ID: 20260729_0011
Revises: 20260729_0010
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260729_0011"
down_revision: Union[str, Sequence[str], None] = "20260729_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "validaciones_administrativas",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("expediente_id", sa.String(32), nullable=False),
        sa.Column("resultado", sa.String(64), nullable=False),
        sa.Column("usuario", sa.String(255), nullable=False),
        sa.Column("fecha_validacion", sa.DateTime(), nullable=False),
        sa.Column("motivo_observacion", sa.Text(), nullable=True),
        sa.Column("estado_expediente", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "resultado IN "
            "('VALIDADA', 'VALIDADA_CON_OBSERVACIONES')",
            name="ck_validaciones_administrativas_resultado",
        ),
        sa.CheckConstraint(
            "(resultado = 'VALIDADA' AND motivo_observacion IS NULL) "
            "OR (resultado = 'VALIDADA_CON_OBSERVACIONES' "
            "AND motivo_observacion IS NOT NULL "
            "AND length(trim(motivo_observacion)) > 0)",
            name="ck_validaciones_administrativas_motivo",
        ),
        sa.ForeignKeyConstraint(
            ["expediente_id"],
            ["expedientes.id"],
            name="fk_validaciones_administrativas_expediente",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_validaciones_administrativas",
        ),
    )
    op.create_index(
        "ix_validaciones_administrativas_expediente_fecha",
        "validaciones_administrativas",
        ["expediente_id", "fecha_validacion", "id"],
        unique=False,
    )
    op.create_table(
        "validacion_controles",
        sa.Column("validacion_id", sa.Integer(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(255), nullable=False),
        sa.Column("estado", sa.String(64), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "orden >= 0",
            name="ck_validacion_controles_orden",
        ),
        sa.ForeignKeyConstraint(
            ["validacion_id"],
            ["validaciones_administrativas.id"],
            name="fk_validacion_controles_validacion",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "validacion_id",
            "orden",
            name="pk_validacion_controles",
        ),
    )


def downgrade() -> None:
    op.drop_table("validacion_controles")
    op.drop_index(
        "ix_validaciones_administrativas_expediente_fecha",
        table_name="validaciones_administrativas",
    )
    op.drop_table("validaciones_administrativas")
