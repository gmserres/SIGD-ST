from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.decision_administrativa_model import DecisionAdministrativaModel
from app.infrastructure.database.models.proveedor_model import ProveedorModel
from app.infrastructure.database.models.solicitud_intervencion_model import SolicitudIntervencionModel


class SeleccionProveedorModel(Base):
    __tablename__ = "selecciones_proveedor"
    __table_args__ = (
        Index("ix_selecciones_proveedor_solicitud", "solicitud_intervencion_id"),
        Index("ix_selecciones_proveedor_decision", "decision_administrativa_id"),
        Index("ix_selecciones_proveedor_proveedor", "proveedor_id"),
        Index("ix_selecciones_proveedor_fecha", "fecha_seleccion"),
        Index(
            "uq_selecciones_proveedor_solicitud_vigente",
            "solicitud_intervencion_id",
            unique=True,
            postgresql_where=text("vigente IS TRUE"),
            sqlite_where=text("vigente = 1"),
        ),
    )

    id_seleccion: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    solicitud_intervencion_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey(SolicitudIntervencionModel.id_solicitud, ondelete="RESTRICT"),
        nullable=False,
    )
    decision_administrativa_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey(DecisionAdministrativaModel.id_decision, ondelete="RESTRICT"),
        nullable=False,
    )
    proveedor_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey(ProveedorModel.id_proveedor, ondelete="RESTRICT"),
        nullable=False,
    )
    fecha_seleccion: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    seleccionado_por: Mapped[str] = mapped_column(String(255), nullable=False)
    proveedor_cuit: Mapped[str] = mapped_column(String(11), nullable=False)
    proveedor_razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    motivo_reemplazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False)
