from typing import Optional
from pydantic import BaseModel, Field

class EstablecimientoCreate(BaseModel):
    tipo: str = Field(..., examples=["EP"])
    numero: str = Field(..., examples=["2"])
    nombre_abreviado: str = Field(..., examples=["EP N° 2"])
    nombre_completo: Optional[str] = None

class EstablecimientoRead(BaseModel):
    id: str
    tipo: str
    numero: str
    nombre_abreviado: str
    nombre_completo: Optional[str] = None
