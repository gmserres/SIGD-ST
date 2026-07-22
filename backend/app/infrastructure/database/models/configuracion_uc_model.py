from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class ConfiguracionUCModel(Base):
    __tablename__ = "configuraciones_uc"
    __table_args__ = (
        CheckConstraint(
            "valor_uc > 0",
            name="ck_configuraciones_uc_valor_positivo",
        ),
        CheckConstraint(
            (
                "fecha_fin_vigencia IS NULL "
                "OR fecha_fin_vigencia >= fecha_inicio_vigencia"
            ),
            name="ck_configuraciones_uc_vigencia_coherente",
        ),
        Index(
            "ix_configuraciones_uc_vigencia",
            "fecha_inicio_vigencia",
            "fecha_fin_vigencia",
        ),
    )

    id_configuracion: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    fecha_inicio_vigencia: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    fecha_fin_vigencia: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    valor_uc: Mapped[Decimal] = mapped_column(
        Numeric(20, 6),
        nullable=False,
    )
    moneda: Mapped[str] = mapped_column(String(16), nullable=False)
    resolucion: Mapped[str] = mapped_column(Text, nullable=False)
    organismo_emisor: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(String(64), nullable=False)

    rangos: Mapped[list[RangoProcedimientoUCModel]] = relationship(
        back_populates="configuracion",
        cascade="all, delete-orphan",
        order_by="RangoProcedimientoUCModel.orden",
        lazy="selectin",
    )


class RangoProcedimientoUCModel(Base):
    __tablename__ = "configuraciones_uc_rangos"
    __table_args__ = (
        CheckConstraint(
            "limite_superior > limite_inferior",
            name="ck_configuraciones_uc_rangos_limites_coherentes",
        ),
        CheckConstraint(
            "orden >= 0",
            name="ck_configuraciones_uc_rangos_orden_no_negativo",
        ),
    )

    id_rango: Mapped[str] = mapped_column(String(64), primary_key=True)
    configuracion_uc_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey(
            "configuraciones_uc.id_configuracion",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    limite_inferior: Mapped[Decimal] = mapped_column(
        Numeric(20, 6),
        nullable=False,
    )
    limite_superior: Mapped[Decimal] = mapped_column(
        Numeric(20, 6),
        nullable=False,
    )
    limite_inferior_inclusivo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    limite_superior_inclusivo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    procedimiento: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    articulo: Mapped[str] = mapped_column(String(64), nullable=False)
    inciso: Mapped[str] = mapped_column(String(64), nullable=False)
    referencia_normativa: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False)

    configuracion: Mapped[ConfiguracionUCModel] = relationship(
        back_populates="rangos",
    )
