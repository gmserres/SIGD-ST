"""Cierre y desistimiento de Expediente.

Revision ID: 20260818_0021
Revises: 20260818_0020
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260818_0021"
down_revision: Union[str, Sequence[str], None] = "20260818_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("expedientes", sa.Column("fecha_cierre", sa.Date(), nullable=True))
    op.add_column("expedientes", sa.Column("usuario_registro_cierre", sa.String(length=255), nullable=True))
    op.add_column("expedientes", sa.Column("registrado_cierre_en", sa.DateTime(), nullable=True))
    op.add_column("expedientes", sa.Column("fecha_desistimiento", sa.Date(), nullable=True))
    op.add_column("expedientes", sa.Column("usuario_registro_desistimiento", sa.String(length=255), nullable=True))
    op.add_column("expedientes", sa.Column("registrado_desistimiento_en", sa.DateTime(), nullable=True))
    op.add_column("expedientes", sa.Column("motivo_desistimiento", sa.Text(), nullable=True))

    op.create_check_constraint(
        "ck_expedientes_cierre_completo",
        "expedientes",
        "(fecha_cierre IS NULL AND usuario_registro_cierre IS NULL AND registrado_cierre_en IS NULL) OR "
        "(fecha_cierre IS NOT NULL AND usuario_registro_cierre IS NOT NULL AND registrado_cierre_en IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_expedientes_desistimiento_completo",
        "expedientes",
        "(fecha_desistimiento IS NULL AND usuario_registro_desistimiento IS NULL AND "
        "registrado_desistimiento_en IS NULL AND motivo_desistimiento IS NULL) OR "
        "(fecha_desistimiento IS NOT NULL AND usuario_registro_desistimiento IS NOT NULL AND "
        "registrado_desistimiento_en IS NOT NULL AND motivo_desistimiento IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_expedientes_motivo_desistimiento_no_vacio",
        "expedientes",
        "motivo_desistimiento IS NULL OR length(trim(motivo_desistimiento)) > 0",
    )
    op.create_check_constraint(
        "ck_expedientes_finalizaciones_exclusivas",
        "expedientes",
        "NOT (fecha_cierre IS NOT NULL AND fecha_desistimiento IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_expedientes_estado_finalizacion",
        "expedientes",
        "(estado = 'CERRADO' AND fecha_cierre IS NOT NULL AND fecha_desistimiento IS NULL) OR "
        "(estado = 'DESISTIDO' AND fecha_desistimiento IS NOT NULL AND fecha_cierre IS NULL) OR "
        "(estado = 'ARCHIVADO' AND NOT (fecha_cierre IS NOT NULL AND fecha_desistimiento IS NOT NULL)) OR "
        "(estado NOT IN ('CERRADO', 'DESISTIDO', 'ARCHIVADO') AND fecha_cierre IS NULL AND fecha_desistimiento IS NULL)",
    )


def downgrade() -> None:
    conexion = op.get_bind()
    cantidad = conexion.scalar(sa.text(
        "SELECT count(*) FROM expedientes WHERE estado IN ('CERRADO', 'DESISTIDO') "
        "OR fecha_cierre IS NOT NULL OR usuario_registro_cierre IS NOT NULL "
        "OR registrado_cierre_en IS NOT NULL OR fecha_desistimiento IS NOT NULL "
        "OR usuario_registro_desistimiento IS NOT NULL OR registrado_desistimiento_en IS NOT NULL "
        "OR motivo_desistimiento IS NOT NULL"
    ))
    if cantidad:
        raise RuntimeError(
            "No puede revertirse F6D2A mientras existan cierres o desistimientos registrados."
        )
    op.drop_constraint("ck_expedientes_estado_finalizacion", "expedientes", type_="check")
    op.drop_constraint("ck_expedientes_finalizaciones_exclusivas", "expedientes", type_="check")
    op.drop_constraint("ck_expedientes_motivo_desistimiento_no_vacio", "expedientes", type_="check")
    op.drop_constraint("ck_expedientes_desistimiento_completo", "expedientes", type_="check")
    op.drop_constraint("ck_expedientes_cierre_completo", "expedientes", type_="check")
    op.drop_column("expedientes", "motivo_desistimiento")
    op.drop_column("expedientes", "registrado_desistimiento_en")
    op.drop_column("expedientes", "usuario_registro_desistimiento")
    op.drop_column("expedientes", "fecha_desistimiento")
    op.drop_column("expedientes", "registrado_cierre_en")
    op.drop_column("expedientes", "usuario_registro_cierre")
    op.drop_column("expedientes", "fecha_cierre")
