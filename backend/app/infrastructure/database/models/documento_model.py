from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)


class DocumentoModel(Base):
    __tablename__ = "documentos"
    __table_args__ = (
        Index(
            "ix_documentos_expediente_fecha",
            "expediente_id",
            "fecha_carga",
            "secuencia",
        ),
    )

    secuencia: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    expediente_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey(ExpedienteModel.id, ondelete="RESTRICT"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre_archivo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    ruta: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_carga: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    tamano_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    mime_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    @property
    def id(self) -> str:
        return f"DOC-{self.secuencia:06d}"
