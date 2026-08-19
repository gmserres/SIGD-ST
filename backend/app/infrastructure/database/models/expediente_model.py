from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.configuracion_uc_model import (
    ConfiguracionUCModel,
)


expedientes_id_sequence = Sequence("expedientes_id_seq")


class ExpedienteModel(Base):
    __tablename__ = "expedientes"
    __table_args__ = (
        Index("ix_expedientes_solicitud", "solicitud_intervencion_id"),
        Index("ix_expedientes_decision", "decision_administrativa_id"),
        Index("ix_expedientes_configuracion_uc", "configuracion_uc_id"),
        Index("ix_expedientes_id_suna", "id_suna"),
        Index("ix_expedientes_estado", "estado"),
        CheckConstraint(
            "(fecha_cierre IS NULL AND usuario_registro_cierre IS NULL AND registrado_cierre_en IS NULL) OR "
            "(fecha_cierre IS NOT NULL AND usuario_registro_cierre IS NOT NULL AND registrado_cierre_en IS NOT NULL)",
            name="ck_expedientes_cierre_completo",
        ),
        CheckConstraint(
            "(fecha_desistimiento IS NULL AND usuario_registro_desistimiento IS NULL AND registrado_desistimiento_en IS NULL AND motivo_desistimiento IS NULL) OR "
            "(fecha_desistimiento IS NOT NULL AND usuario_registro_desistimiento IS NOT NULL AND registrado_desistimiento_en IS NOT NULL AND motivo_desistimiento IS NOT NULL)",
            name="ck_expedientes_desistimiento_completo",
        ),
        CheckConstraint(
            "motivo_desistimiento IS NULL OR length(trim(motivo_desistimiento)) > 0",
            name="ck_expedientes_motivo_desistimiento_no_vacio",
        ),
        CheckConstraint(
            "NOT (fecha_cierre IS NOT NULL AND fecha_desistimiento IS NOT NULL)",
            name="ck_expedientes_finalizaciones_exclusivas",
        ),
        CheckConstraint(
            "(estado = 'CERRADO' AND fecha_cierre IS NOT NULL AND fecha_desistimiento IS NULL) OR "
            "(estado = 'DESISTIDO' AND fecha_desistimiento IS NOT NULL AND fecha_cierre IS NULL) OR "
            "(estado = 'ARCHIVADO' AND NOT (fecha_cierre IS NOT NULL AND fecha_desistimiento IS NOT NULL)) OR "
            "(estado NOT IN ('CERRADO', 'DESISTIDO', 'ARCHIVADO') AND fecha_cierre IS NULL AND fecha_desistimiento IS NULL)",
            name="ck_expedientes_estado_finalizacion",
        ),
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
    configuracion_uc_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey(
            ConfiguracionUCModel.id_configuracion,
            ondelete="RESTRICT",
        ),
        nullable=True,
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
    fecha_firma: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    usuario_registro_firma: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    fecha_archivo: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    usuario_registro_archivo: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    fecha_cierre: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario_registro_cierre: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    registrado_cierre_en: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    fecha_desistimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario_registro_desistimiento: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    registrado_desistimiento_en: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    motivo_desistimiento: Mapped[str | None] = mapped_column(Text, nullable=True)
