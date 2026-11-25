"""Autenticacion, usuarios y sesiones.

Revision ID: 20261110_0022
Revises: 20260818_0021
Create Date: 2026-11-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261110_0022"
down_revision: Union[str, Sequence[str], None] = "20260818_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("rol", sa.String(length=32), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "rol IN ('ADMINISTRADOR', 'SECRETARIO_TECNICO', 'OPERADOR', 'CONSULTA')",
            name="ck_usuarios_rol",
        ),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)
    op.create_table(
        "sesiones_usuario",
        sa.Column("token_hash", sa.String(length=64), primary_key=True),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("creada_en", sa.DateTime(), nullable=False),
        sa.Column("expira_en", sa.DateTime(), nullable=False),
        sa.Column("revocada_en", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sesiones_usuario_usuario_id", "sesiones_usuario", ["usuario_id"])
    op.create_index("ix_sesiones_usuario_expira_en", "sesiones_usuario", ["expira_en"])


def downgrade() -> None:
    op.drop_index("ix_sesiones_usuario_expira_en", table_name="sesiones_usuario")
    op.drop_index("ix_sesiones_usuario_usuario_id", table_name="sesiones_usuario")
    op.drop_table("sesiones_usuario")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
