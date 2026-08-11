"""Preparar Disposición para cardinalidad por OP.

Revision ID: 20260811_0018
Revises: 20260811_0017
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260811_0018"
down_revision: Union[str, Sequence[str], None] = "20260811_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "disposiciones",
        sa.Column("documento_op_secuencia", sa.Integer(), nullable=True),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "control_proveedor_op_id",
            sa.Uuid(as_uuid=False),
            nullable=True,
        ),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "seleccion_proveedor_id",
            sa.Uuid(as_uuid=False),
            nullable=True,
        ),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "proveedor_definitivo_id",
            sa.Uuid(as_uuid=False),
            nullable=True,
        ),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "proveedor_definitivo_cuit",
            sa.String(length=11),
            nullable=True,
        ),
    )
    op.add_column(
        "disposiciones",
        sa.Column(
            "proveedor_definitivo_razon_social",
            sa.Text(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_disposiciones_documento_op",
        "disposiciones",
        "documentos",
        ["documento_op_secuencia"],
        ["secuencia"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_disposiciones_control_proveedor_op",
        "disposiciones",
        "controles_proveedor_op",
        ["control_proveedor_op_id"],
        ["id_control"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_disposiciones_seleccion_proveedor",
        "disposiciones",
        "selecciones_proveedor",
        ["seleccion_proveedor_id"],
        ["id_seleccion"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_disposiciones_proveedor_definitivo",
        "disposiciones",
        "proveedores",
        ["proveedor_definitivo_id"],
        ["id_proveedor"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "uq_disposiciones_expediente",
        "disposiciones",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_disposiciones_documento_op",
        "disposiciones",
        ["documento_op_secuencia"],
    )
    op.create_index(
        "ix_disposiciones_expediente",
        "disposiciones",
        ["expediente_id"],
        unique=False,
    )
    op.create_index(
        "ix_disposiciones_control_proveedor_op",
        "disposiciones",
        ["control_proveedor_op_id"],
        unique=False,
    )
    op.create_index(
        "ix_disposiciones_seleccion_proveedor",
        "disposiciones",
        ["seleccion_proveedor_id"],
        unique=False,
    )
    op.create_index(
        "ix_disposiciones_proveedor_definitivo",
        "disposiciones",
        ["proveedor_definitivo_id"],
        unique=False,
    )


def downgrade() -> None:
    duplicado = op.get_bind().execute(
        sa.text(
            """
            SELECT expediente_id, COUNT(*) AS cantidad
            FROM disposiciones
            GROUP BY expediente_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).mappings().first()
    if duplicado is not None:
        raise RuntimeError(
            "No puede restaurarse la cardinalidad legacy: el "
            f"Expediente {duplicado['expediente_id']} posee "
            f"{duplicado['cantidad']} Disposiciones."
        )

    for indice in (
        "ix_disposiciones_proveedor_definitivo",
        "ix_disposiciones_seleccion_proveedor",
        "ix_disposiciones_control_proveedor_op",
        "ix_disposiciones_expediente",
    ):
        op.drop_index(indice, table_name="disposiciones")
    op.drop_constraint(
        "uq_disposiciones_documento_op",
        "disposiciones",
        type_="unique",
    )
    for restriccion in (
        "fk_disposiciones_proveedor_definitivo",
        "fk_disposiciones_seleccion_proveedor",
        "fk_disposiciones_control_proveedor_op",
        "fk_disposiciones_documento_op",
    ):
        op.drop_constraint(
            restriccion,
            "disposiciones",
            type_="foreignkey",
        )
    for columna in (
        "proveedor_definitivo_razon_social",
        "proveedor_definitivo_cuit",
        "proveedor_definitivo_id",
        "seleccion_proveedor_id",
        "control_proveedor_op_id",
        "documento_op_secuencia",
    ):
        op.drop_column("disposiciones", columna)
    op.create_unique_constraint(
        "uq_disposiciones_expediente",
        "disposiciones",
        ["expediente_id"],
    )
