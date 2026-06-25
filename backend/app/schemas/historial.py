from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class HistorialRead(BaseModel):
    id: str
    expediente_id: str
    accion: str
    usuario: str
    fecha: datetime
    detalle: Optional[str] = None
