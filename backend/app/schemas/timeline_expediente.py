from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TipoEventoTimeline = Literal[
    "EXPEDIENTE_CREADO",
    "DOCUMENTO_INCORPORADO",
    "OP_INCORPORADA",
    "CHECKLIST_FISICO_REGISTRADO",
    "VALIDACION_ADMINISTRATIVA",
    "VALIDACION_ADMINISTRATIVA_INVALIDADA",
    "PROVEEDOR_SELECCIONADO",
    "PROVEEDOR_REEMPLAZADO",
    "CONTROL_PROVEEDOR_OP",
    "DISPOSICION_EMITIDA",
    "DISPOSICION_FORMALIZADA",
    "EXPEDIENTE_CERRADO",
    "EXPEDIENTE_DESISTIDO",
    "EXPEDIENTE_ARCHIVADO",
]


class EventoTimelineExpedienteRead(BaseModel):
    tipo: TipoEventoTimeline
    fecha_hora: datetime
    titulo: str
    descripcion: str | None = None
    usuario: str | None = None
    entidad_origen: str
    entidad_origen_id: str
    documento_op_id: str | None = None
    metadatos: dict[str, str | int | bool | None] = Field(
        default_factory=dict
    )
