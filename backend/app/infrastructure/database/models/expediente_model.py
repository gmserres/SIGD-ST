from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Sequence, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


expedientes_id_sequence = Sequence("expedientes_id_seq")


class ExpedienteModel(Base):
    __tablename__ = "expedientes"
    __table_args__ = (
        Index("ix_expedientes_solicitud", "solicitud_intervencion_id"),
        Index("ix_expedientes_decision", "decision_administrativa_id"),
        Index("ix_expedientes_id_suna", "id_suna"),
        Index("ix_expedientes_estado", "estado"),
    )

    secuencia: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    numero_interno: Mapped[str] = mapped_column(String(255), nullable=False)
    numero_gdeba: Mapped[str | None] = mapped_column(String(255), nullable=True)
    solicitud_intervencion_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    decision_administrativa_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    id_suna: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tipo_tramite: Mapped[str] = mapped_column(String(64), nullable=False)
    estado: Mapped[str] = mapped_column(String(64), nullable=False)
    establecimiento: Mapped[str | None] = mapped_column(Text, nullable=True)
    objeto: Mapped[str | None] = mapped_column(Text, nullable=True)
    numero_disposicion: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    creado: Mapped[datetime] = mapped_column(DateTime, nullable=False)
