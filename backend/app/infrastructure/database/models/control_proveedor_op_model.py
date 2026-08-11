from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Sequence,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.seleccion_proveedor_model import (
    SeleccionProveedorModel,
)
from app.infrastructure.database.models.solicitud_intervencion_model import (
    SolicitudIntervencionModel,
)


control_proveedor_op_secuencia = Sequence(
    "controles_proveedor_op_secuencia_seq"
)


class ControlProveedorOPModel(Base):
    __tablename__ = "controles_proveedor_op"
    __table_args__ = (
        CheckConstraint(
            "estado IN "
            "('COINCIDE', 'CUIT_DIFERENTE', 'NO_VERIFICABLE')",
            name="ck_controles_proveedor_op_estado",
        ),
        Index(
            "ix_controles_proveedor_op_documento_secuencia",
            "documento_secuencia",
            "secuencia",
        ),
        Index(
            "ix_controles_proveedor_op_seleccion",
            "seleccion_proveedor_id",
        ),
    )

    id_control: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
    )
    secuencia: Mapped[int] = mapped_column(
        Integer,
        control_proveedor_op_secuencia,
        unique=True,
        nullable=False,
    )
    expediente_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey(ExpedienteModel.id, ondelete="RESTRICT"),
        nullable=False,
    )
    documento_secuencia: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(DocumentoModel.secuencia, ondelete="RESTRICT"),
        nullable=False,
    )
    solicitud_intervencion_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey(
            SolicitudIntervencionModel.id_solicitud,
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    seleccion_proveedor_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey(
            SeleccionProveedorModel.id_seleccion,
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(String(64), nullable=False)
    proveedor_cuit_seleccionado: Mapped[str] = mapped_column(
        String(11), nullable=False
    )
    proveedor_razon_social_seleccionada: Mapped[str] = (
        mapped_column(String(255), nullable=False)
    )
    cuit_detectado: Mapped[str | None] = mapped_column(
        String(11), nullable=True
    )
    razon_social_detectada: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    advertencias: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )
    fecha_control: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    modo_analisis: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
