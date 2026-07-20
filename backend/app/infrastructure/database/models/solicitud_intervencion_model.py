from datetime import date

from sqlalchemy import Date, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SolicitudIntervencionModel(Base):
    __tablename__ = "solicitudes_intervencion"
    __table_args__ = (
        UniqueConstraint(
            "numero_solicitud",
            name="uq_solicitudes_intervencion_numero_solicitud",
        ),
    )

    id_solicitud: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
    )
    numero_solicitud: Mapped[str] = mapped_column(String(), nullable=False)
    procedencia: Mapped[str] = mapped_column(String(), nullable=False)
    id_suna: Mapped[str | None] = mapped_column(String(), nullable=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    establecimiento: Mapped[str] = mapped_column(String(), nullable=False)
    solicitante: Mapped[str] = mapped_column(String(), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    prioridad: Mapped[str] = mapped_column(String(), nullable=False)
    estado: Mapped[str] = mapped_column(String(), nullable=False)
