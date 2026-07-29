from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)


class ValidacionAdministrativaModel(Base):
    __tablename__ = "validaciones_administrativas"
    __table_args__ = (
        CheckConstraint(
            "resultado IN "
            "('VALIDADA', 'VALIDADA_CON_OBSERVACIONES')",
            name="ck_validaciones_administrativas_resultado",
        ),
        CheckConstraint(
            "(resultado = 'VALIDADA' AND motivo_observacion IS NULL) "
            "OR (resultado = 'VALIDADA_CON_OBSERVACIONES' "
            "AND motivo_observacion IS NOT NULL "
            "AND length(trim(motivo_observacion)) > 0)",
            name="ck_validaciones_administrativas_motivo",
        ),
        CheckConstraint(
            "(fecha_invalidacion IS NULL "
            "AND motivo_invalidacion IS NULL "
            "AND usuario_invalidacion IS NULL) "
            "OR (fecha_invalidacion IS NOT NULL "
            "AND motivo_invalidacion IS NOT NULL "
            "AND usuario_invalidacion IS NOT NULL)",
            name="ck_validaciones_administrativas_invalidacion_completa",
        ),
        Index(
            "ix_validaciones_administrativas_expediente_fecha",
            "expediente_id",
            "fecha_validacion",
            "id",
        ),
        Index(
            "uq_validaciones_administrativas_vigente",
            "expediente_id",
            unique=True,
            postgresql_where=text("fecha_invalidacion IS NULL"),
            sqlite_where=text("fecha_invalidacion IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    expediente_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey(ExpedienteModel.id, ondelete="RESTRICT"),
        nullable=False,
    )
    resultado: Mapped[str] = mapped_column(String(64), nullable=False)
    usuario: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_validacion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    motivo_observacion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    estado_expediente: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    fecha_invalidacion: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    motivo_invalidacion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    usuario_invalidacion: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    controles: Mapped[list["ValidacionControlModel"]] = relationship(
        back_populates="validacion",
        cascade="all, delete-orphan",
        order_by="ValidacionControlModel.orden",
    )


class ValidacionControlModel(Base):
    __tablename__ = "validacion_controles"
    __table_args__ = (
        CheckConstraint(
            "orden >= 0",
            name="ck_validacion_controles_orden",
        ),
    )

    validacion_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "validaciones_administrativas.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    orden: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(64), nullable=False)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    validacion: Mapped[ValidacionAdministrativaModel] = relationship(
        back_populates="controles",
    )
