from datetime import datetime
from pydantic import BaseModel


class DisposicionRead(BaseModel):
    expediente_id: str
    numero_disposicion: str | None
    estado: str
    visto: str
    considerando: str
    dispone: str
    observaciones_ia: list[str]
    creado: datetime
    actualizado: datetime


class DisposicionUpdate(BaseModel):
    visto: str | None = None
    considerando: str | None = None
    dispone: str | None = None
