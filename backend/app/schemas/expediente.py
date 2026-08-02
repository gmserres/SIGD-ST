from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.estados import EstadoExpediente


class ExpedienteCreate(BaseModel):
    numero_interno: str = Field(..., examples=["033-188/2025"])
    numero_gdeba: Optional[str] = Field(default=None)
    solicitud_intervencion_id: str | None = None
    decision_administrativa_id: str | None = None
    configuracion_uc_id: str | None = None
    id_suna: Optional[str] = Field(default=None, examples=["45872"])
    tipo_tramite: str = Field(default="FONDO_COMPENSADOR")
    establecimiento: Optional[str] = Field(default=None, examples=["EP N° 2"])
    objeto: Optional[str] = Field(default=None, examples=["Recambio total de cañerías de agua fría"])
    numero_disposicion: Optional[str] = Field(default=None, examples=["201/2025"])


class ExpedienteUpdate(BaseModel):
    id_suna: Optional[str] = None
    establecimiento: Optional[str] = None
    objeto: Optional[str] = None
    numero_disposicion: Optional[str] = None


class ExpedienteRead(BaseModel):
    id: str
    numero_interno: str
    numero_gdeba: Optional[str]
    solicitud_intervencion_id: str | None = None
    decision_administrativa_id: str | None = None
    configuracion_uc_id: str | None = None
    id_suna: Optional[str]
    tipo_tramite: str
    estado: EstadoExpediente
    establecimiento: Optional[str]
    objeto: Optional[str]
    numero_disposicion: Optional[str]
    creado: datetime
    fecha_firma: date | None = None
    usuario_registro_firma: str | None = None
    fecha_archivo: date | None = None
    usuario_registro_archivo: str | None = None
