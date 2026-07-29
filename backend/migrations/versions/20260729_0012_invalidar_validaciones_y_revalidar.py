"""Agregar vigencia e invalidación de validaciones administrativas.

Revision ID: 20260729_0012
Revises: 20260729_0011
Create Date: 2026-07-29
"""
from collections import defaultdict
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260729_0012"
down_revision: Union[str, Sequence[str], None] = "20260729_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MOTIVO_MIGRACION = (
    "Normalización técnica de vigencia — Sprint 0075 Diff 3"
)
USUARIO_MIGRACION = "MIGRACION_0075"


def upgrade() -> None:
    op.add_column(
        "validaciones_administrativas",
        sa.Column(
            "fecha_invalidacion",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "validaciones_administrativas",
        sa.Column(
            "motivo_invalidacion",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "validaciones_administrativas",
        sa.Column(
            "usuario_invalidacion",
            sa.String(255),
            nullable=True,
        ),
    )

    _normalizar_validaciones_existentes(op.get_bind())

    op.create_check_constraint(
        "ck_validaciones_administrativas_invalidacion_completa",
        "validaciones_administrativas",
        "(fecha_invalidacion IS NULL "
        "AND motivo_invalidacion IS NULL "
        "AND usuario_invalidacion IS NULL) "
        "OR (fecha_invalidacion IS NOT NULL "
        "AND motivo_invalidacion IS NOT NULL "
        "AND usuario_invalidacion IS NOT NULL)",
    )

    op.create_index(
        "uq_validaciones_administrativas_vigente",
        "validaciones_administrativas",
        ["expediente_id"],
        unique=True,
        postgresql_where=sa.text("fecha_invalidacion IS NULL"),
        sqlite_where=sa.text("fecha_invalidacion IS NULL"),
    )


def _normalizar_validaciones_existentes(bind) -> None:
    filas = bind.execute(
        sa.text(
            "SELECT id, expediente_id, fecha_validacion "
            "FROM validaciones_administrativas "
            "ORDER BY expediente_id, fecha_validacion, id"
        )
    ).mappings()
    por_expediente: dict[str, list[dict]] = defaultdict(list)
    for fila in filas:
        por_expediente[fila["expediente_id"]].append(dict(fila))

    for actos in por_expediente.values():
        for posicion, acto in enumerate(actos[:-1]):
            acto_posterior = actos[posicion + 1]
            bind.execute(
                sa.text(
                    "UPDATE validaciones_administrativas "
                    "SET fecha_invalidacion = :fecha, "
                    "motivo_invalidacion = :motivo, "
                    "usuario_invalidacion = :usuario "
                    "WHERE id = :id"
                ),
                {
                    "fecha": acto_posterior["fecha_validacion"],
                    "motivo": MOTIVO_MIGRACION,
                    "usuario": USUARIO_MIGRACION,
                    "id": acto["id"],
                },
            )

def downgrade() -> None:
    op.drop_index(
        "uq_validaciones_administrativas_vigente",
        table_name="validaciones_administrativas",
    )
    op.drop_constraint(
        "ck_validaciones_administrativas_invalidacion_completa",
        "validaciones_administrativas",
        type_="check",
    )
    op.drop_column(
        "validaciones_administrativas",
        "usuario_invalidacion",
    )
    op.drop_column(
        "validaciones_administrativas",
        "motivo_invalidacion",
    )
    op.drop_column(
        "validaciones_administrativas",
        "fecha_invalidacion",
    )
