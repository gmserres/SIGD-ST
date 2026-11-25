from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    rol: Mapped[str] = mapped_column(String(32), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SesionUsuarioModel(Base):
    __tablename__ = "sesiones_usuario"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    creada_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expira_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
