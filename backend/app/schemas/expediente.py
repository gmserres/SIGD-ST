from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.estados import EstadoExpediente


class ExpedienteCreate(BaseModel):
    numero_interno: str = Field(..., examples=["033-188/2025"])
    tipo_tramite: str = Field(default="FONDO_COMPENSADOR")
    establecimiento: Optional[str] = Field(default=None, examples=["EP N° 2"])
    objeto: Optional[str] = Field(default=None, examples=["Recambio total de cañerías de agua fría"])
    numero_disposicion: Optional[str] = Field(default=None, examples=["201/2025"])


class ExpedienteUpdate(BaseModel):
    establecimiento: Optional[str] = None
    objeto: Optional[str] = None
    numero_disposicion: Optional[str] = None


class ExpedienteRead(BaseModel):
    id: str
    numero_interno: str
    tipo_tramite: str
    estado: EstadoExpediente
    establecimiento: Optional[str]
    objeto: Optional[str]
    numero_disposicion: Optional[str]
    creado: datetime
