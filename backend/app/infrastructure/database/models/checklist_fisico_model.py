from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)


class ChecklistFisicoModel(Base):
    __tablename__ = "checklists_fisicos"
    __table_args__ = (
        UniqueConstraint(
            "expediente_id",
            name="uq_checklists_fisicos_expediente",
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
    factura: Mapped[bool] = mapped_column(Boolean, nullable=False)
    remito_conformidad: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    cae: Mapped[bool] = mapped_column(Boolean, nullable=False)
    arca: Mapped[bool] = mapped_column(Boolean, nullable=False)
    arba: Mapped[bool] = mapped_column(Boolean, nullable=False)
    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    usuario: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
