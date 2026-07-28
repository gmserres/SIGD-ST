from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.configuracion_uc_model import (
    ConfiguracionUCModel,
)
from app.infrastructure.database.models.expediente_model import ExpedienteModel


class DisposicionModel(Base):
    __tablename__ = "disposiciones"
    __table_args__ = (
        UniqueConstraint(
            "expediente_id",
            name="uq_disposiciones_expediente",
        ),
        UniqueConstraint(
            "numero_disposicion",
            name="uq_disposiciones_numero",
        ),
        Index("ix_disposiciones_configuracion_uc", "configuracion_uc_id"),
        Index("ix_disposiciones_fecha_emision", "fecha_emision"),
        Index("ix_disposiciones_numero_op", "numero_op"),
    )

    id_disposicion: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
    )
    expediente_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey(ExpedienteModel.id, ondelete="RESTRICT"),
        nullable=False,
    )
    configuracion_uc_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey(
            ConfiguracionUCModel.id_configuracion,
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    numero_disposicion: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    fondo_interviniente: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    numero_op: Mapped[str] = mapped_column(String(255), nullable=False)
    numero_liquidacion: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    proveedor: Mapped[str] = mapped_column(String(255), nullable=False)
    cuit: Mapped[str] = mapped_column(String(32), nullable=False)
    importe: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    objeto: Mapped[str] = mapped_column(Text, nullable=False)
    establecimiento: Mapped[str] = mapped_column(Text, nullable=False)
    valor_uc_aplicado: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False
    )
    cantidad_uc: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), nullable=False
    )
    procedimiento_contratacion: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    norma_uc: Mapped[str] = mapped_column(Text, nullable=False)
    texto_emitido: Mapped[str] = mapped_column(Text, nullable=False)
    ruta_docx: Mapped[str] = mapped_column(Text, nullable=False)
