"""Crear configuraciones UC y sus rangos.

Revision ID: 20260722_0003
Revises: 20260720_0002
Create Date: 2026-07-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260722_0003"
down_revision: Union[str, Sequence[str], None] = "20260720_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "configuraciones_uc",
        sa.Column(
            "id_configuracion",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "fecha_inicio_vigencia",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "fecha_fin_vigencia",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "valor_uc",
            sa.Numeric(precision=20, scale=6),
            nullable=False,
        ),
        sa.Column("moneda", sa.String(length=16), nullable=False),
        sa.Column("resolucion", sa.Text(), nullable=False),
        sa.Column(
            "organismo_emisor",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("estado", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "valor_uc > 0",
            name="ck_configuraciones_uc_valor_positivo",
        ),
        sa.CheckConstraint(
            (
                "fecha_fin_vigencia IS NULL "
                "OR fecha_fin_vigencia >= fecha_inicio_vigencia"
            ),
            name="ck_configuraciones_uc_vigencia_coherente",
        ),
        sa.PrimaryKeyConstraint(
            "id_configuracion",
            name="pk_configuraciones_uc",
        ),
    )
    op.create_index(
        "ix_configuraciones_uc_vigencia",
        "configuraciones_uc",
        ["fecha_inicio_vigencia", "fecha_fin_vigencia"],
        unique=False,
    )

    op.create_table(
        "configuraciones_uc_rangos",
        sa.Column("id_rango", sa.String(length=64), nullable=False),
        sa.Column(
            "configuracion_uc_id",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "limite_inferior",
            sa.Numeric(precision=20, scale=6),
            nullable=False,
        ),
        sa.Column(
            "limite_superior",
            sa.Numeric(precision=20, scale=6),
            nullable=False,
        ),
        sa.Column(
            "limite_inferior_inclusivo",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "limite_superior_inclusivo",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "procedimiento",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("articulo", sa.String(length=64), nullable=False),
        sa.Column("inciso", sa.String(length=64), nullable=False),
        sa.Column(
            "referencia_normativa",
            sa.Text(),
            nullable=False,
        ),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "limite_superior > limite_inferior",
            name="ck_configuraciones_uc_rangos_limites_coherentes",
        ),
        sa.CheckConstraint(
            "orden >= 0",
            name="ck_configuraciones_uc_rangos_orden_no_negativo",
        ),
        sa.ForeignKeyConstraint(
            ["configuracion_uc_id"],
            ["configuraciones_uc.id_configuracion"],
            name="fk_configuraciones_uc_rangos_configuracion",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id_rango",
            name="pk_configuraciones_uc_rangos",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("configuraciones_uc_rangos")
    op.drop_index(
        "ix_configuraciones_uc_vigencia",
        table_name="configuraciones_uc",
    )
    op.drop_table("configuraciones_uc")
