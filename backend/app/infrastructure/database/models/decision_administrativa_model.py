from datetime import date

from sqlalchemy import Date, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class DecisionAdministrativaModel(Base):
    __tablename__ = "decisiones_administrativas"
    __table_args__ = (
        Index(
            "ix_decisiones_administrativas_solicitud",
            "solicitud_intervencion_id",
        ),
    )

    id_decision: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
    )
    solicitud_intervencion_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    autoridad_decisora: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    fecha_decision: Mapped[date] = mapped_column(Date, nullable=False)
    resultado: Mapped[str] = mapped_column(String(255), nullable=False)
    fundamento: Mapped[str] = mapped_column(Text, nullable=False)
    fondo_interviniente: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    descripcion_fondo: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    usuario_registrante: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
