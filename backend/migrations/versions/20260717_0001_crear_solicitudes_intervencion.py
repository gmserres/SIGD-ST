"""crear solicitudes intervencion

Revision ID: 20260717_0001
Revises:
Create Date: 2026-07-17 18:52:36.683579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260717_0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "solicitudes_intervencion",
        sa.Column(
            "id_solicitud",
            postgresql.UUID(as_uuid=False),
            nullable=False,
        ),
        sa.Column("numero_solicitud", sa.String(), nullable=False),
        sa.Column("procedencia", sa.String(), nullable=False),
        sa.Column("id_suna", sa.String(), nullable=True),
        sa.Column("fecha_ingreso", sa.Date(), nullable=False),
        sa.Column("establecimiento", sa.String(), nullable=False),
        sa.Column("solicitante", sa.String(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("prioridad", sa.String(), nullable=False),
        sa.Column("estado", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint(
            "id_solicitud",
            name="pk_solicitudes_intervencion",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("solicitudes_intervencion")
