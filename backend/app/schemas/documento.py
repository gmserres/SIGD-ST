from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentoCreate(BaseModel):
    tipo: str = Field(..., examples=["OP", "FACTURA", "REMITO", "CONFORMIDAD"])
    nombre_archivo: str
    ruta: str
    observaciones: Optional[str] = None
    tamano_bytes: Optional[int] = None
    mime_type: Optional[str] = None


class DocumentoRead(BaseModel):
    id: str
    expediente_id: str
    tipo: str
    nombre_archivo: str
    ruta: str
    fecha_carga: datetime
    observaciones: Optional[str] = None
    tamano_bytes: Optional[int] = None
    mime_type: Optional[str] = None
