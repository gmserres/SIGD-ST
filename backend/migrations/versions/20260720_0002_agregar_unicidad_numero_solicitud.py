"""Agregar unicidad al número de solicitud.

Revision ID: 20260720_0002
Revises: 20260717_0001
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260720_0002"
down_revision: Union[str, Sequence[str], None] = "20260717_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_solicitudes_intervencion_numero_solicitud",
        "solicitudes_intervencion",
        ["numero_solicitud"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_solicitudes_intervencion_numero_solicitud",
        "solicitudes_intervencion",
        type_="unique",
    )
