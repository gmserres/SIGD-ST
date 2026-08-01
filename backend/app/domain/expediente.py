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
