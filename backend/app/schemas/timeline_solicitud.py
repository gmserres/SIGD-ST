from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.timeline_expediente import TipoEventoTimeline


class EventoTimelineSolicitudRead(BaseModel):
    nivel: Literal["SOLICITUD", "EXPEDIENTE"]
    solicitud_id: str
    expediente_id: str | None
    tipo: TipoEventoTimeline | Literal[
        "SOLICITUD_INGRESADA",
        "DECISION_ADMINISTRATIVA",
    ]
    fecha_hora: datetime
    precision_temporal: Literal["FECHA_HORA", "DIA"]
    titulo: str
    descripcion: str | None = None
    usuario: str | None = None
    entidad_origen: str
    entidad_origen_id: str
    documento_op_id: str | None = None
    metadatos: dict[str, str | int | bool | None] = Field(
        default_factory=dict
    )
