from datetime import datetime
from pydantic import BaseModel, Field


class ChecklistFisicoCreate(BaseModel):
    factura: bool = False
    remito_conformidad: bool = False
    cae: bool = False
    arca: bool = False
    arba: bool = False
    observaciones: str | None = Field(default=None)
    usuario: str = Field(default="Secretario Técnico")


class ChecklistFisicoRead(BaseModel):
    expediente_id: str
    factura: bool
    remito_conformidad: bool
    cae: bool
    arca: bool
    arba: bool
    observaciones: str | None = None
    usuario: str
    fecha: datetime
