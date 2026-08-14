"""Asociar SeleccionProveedor a Expediente.

Revision ID: 20260813_0019
Revises: 20260811_0018
Create Date: 2026-08-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0019"
down_revision: Union[str, Sequence[str], None] = "20260811_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _casos_upgrade_no_migrables() -> list[dict]:
    return list(
        op.get_bind()
        .execute(
            sa.text(
                """
                SELECT
                    CAST(s.solicitud_intervencion_id AS TEXT) AS solicitud_id,
                    COUNT(DISTINCT e.id) AS cantidad_expedientes
                FROM selecciones_proveedor AS s
                LEFT JOIN expedientes AS e
                  ON e.solicitud_intervencion_id
                     = CAST(s.solicitud_intervencion_id AS TEXT)
                GROUP BY s.solicitud_intervencion_id
                HAVING COUNT(DISTINCT e.id) <> 1
                ORDER BY CAST(s.solicitud_intervencion_id AS TEXT)
                """
            )
        )
        .mappings()
        .all()
    )


def _casos_downgrade_no_representables() -> list[dict]:
    return list(
        op.get_bind()
        .execute(
            sa.text(
                """
                SELECT
                    CAST(solicitud_intervencion_id AS TEXT) AS solicitud_id,
                    COUNT(*) AS selecciones_vigentes
                FROM selecciones_proveedor
                WHERE vigente IS TRUE
                GROUP BY solicitud_intervencion_id
                HAVING COUNT(*) > 1
                ORDER BY CAST(solicitud_intervencion_id AS TEXT)
                """
            )
        )
        .mappings()
        .all()
    )


def upgrade() -> None:
    casos = _casos_upgrade_no_migrables()
    if casos:
        detalle = ", ".join(
            f"{caso['solicitud_id']}={caso['cantidad_expedientes']}"
            for caso in casos
        )
        raise RuntimeError(
            "No es posible asociar automáticamente SeleccionProveedor "
            f"a Expediente. Solicitudes ambiguas: {detalle}."
        )

    op.add_column(
        "selecciones_proveedor",
        sa.Column("expediente_id", sa.String(length=32), nullable=True),
    )
    op.create_foreign_key(
        "fk_selecciones_proveedor_expediente",
        "selecciones_proveedor",
        "expedientes",
        ["expediente_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.execute(
        sa.text(
            """
            UPDATE selecciones_proveedor AS seleccion
            SET expediente_id = expediente.id
            FROM expedientes AS expediente
            WHERE expediente.solicitud_intervencion_id
                  = CAST(seleccion.solicitud_intervencion_id AS TEXT)
            """
        )
    )
    pendientes = op.get_bind().scalar(
        sa.text(
            "SELECT COUNT(*) FROM selecciones_proveedor "
            "WHERE expediente_id IS NULL"
        )
    )
    if pendientes:
        raise RuntimeError("El backfill dejó selecciones sin Expediente.")

    op.alter_column(
        "selecciones_proveedor",
        "expediente_id",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.create_index(
        "ix_selecciones_proveedor_expediente",
        "selecciones_proveedor",
        ["expediente_id"],
        unique=False,
    )
    op.create_index(
        "uq_selecciones_proveedor_expediente_vigente",
        "selecciones_proveedor",
        ["expediente_id"],
        unique=True,
        postgresql_where=sa.text("vigente IS TRUE"),
    )
    op.drop_index(
        "uq_selecciones_proveedor_solicitud_vigente",
        table_name="selecciones_proveedor",
    )


def downgrade() -> None:
    casos = _casos_downgrade_no_representables()
    if casos:
        detalle = ", ".join(
            f"{caso['solicitud_id']}={caso['selecciones_vigentes']}"
            for caso in casos
        )
        raise RuntimeError(
            "El downgrade no puede representar más de una selección "
            f"vigente por Solicitud: {detalle}."
        )

    op.create_index(
        "uq_selecciones_proveedor_solicitud_vigente",
        "selecciones_proveedor",
        ["solicitud_intervencion_id"],
        unique=True,
        postgresql_where=sa.text("vigente IS TRUE"),
    )
    op.drop_index(
        "uq_selecciones_proveedor_expediente_vigente",
        table_name="selecciones_proveedor",
    )
    op.drop_index(
        "ix_selecciones_proveedor_expediente",
        table_name="selecciones_proveedor",
    )
    op.drop_constraint(
        "fk_selecciones_proveedor_expediente",
        "selecciones_proveedor",
        type_="foreignkey",
    )
    op.drop_column("selecciones_proveedor", "expediente_id")
