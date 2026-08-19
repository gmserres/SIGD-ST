from dataclasses import dataclass
from datetime import date, datetime

from app.domain.estados import EstadoExpediente


@dataclass(frozen=True)
class Expediente:
    id: str
    numero_interno: str
    numero_gdeba: str | None
    solicitud_intervencion_id: str | None
    decision_administrativa_id: str | None
    configuracion_uc_id: str | None
    id_suna: str | None
    tipo_tramite: str
    estado: EstadoExpediente
    establecimiento: str | None
    objeto: str | None
    numero_disposicion: str | None
    creado: datetime
    fecha_firma: date | None = None
    usuario_registro_firma: str | None = None
    fecha_archivo: date | None = None
    usuario_registro_archivo: str | None = None
    fecha_cierre: date | None = None
    usuario_registro_cierre: str | None = None
    registrado_cierre_en: datetime | None = None
    fecha_desistimiento: date | None = None
    usuario_registro_desistimiento: str | None = None
    registrado_desistimiento_en: datetime | None = None
    motivo_desistimiento: str | None = None
