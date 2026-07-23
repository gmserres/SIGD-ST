"""Renombrar norma a resolución en Configuración UC.

Revision ID: 20260722_0006
Revises: 20260722_0005
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0006"
down_revision: Union[str, Sequence[str], None] = "20260722_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columnas_configuraciones_uc() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {
        columna["name"]
        for columna in inspector.get_columns("configuraciones_uc")
    }


def upgrade() -> None:
    columnas = _columnas_configuraciones_uc()

    if "norma" in columnas and "resolucion" not in columnas:
        op.alter_column(
            "configuraciones_uc",
            "norma",
            new_column_name="resolucion",
        )
        return

    if "resolucion" in columnas and "norma" not in columnas:
        return

    raise RuntimeError(
        "No fue posible determinar de forma segura la columna normativa "
        "de configuraciones_uc."
    )


def downgrade() -> None:
    # Migración correctiva de convergencia.
    # La cadena canónica previa ya utiliza `resolucion`, por lo que
    # restaurar `norma` produciría un esquema divergente.
    pass
