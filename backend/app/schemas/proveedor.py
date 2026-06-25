from typing import Optional
from pydantic import BaseModel, Field

class ProveedorCreate(BaseModel):
    cuit: str = Field(..., examples=["30-71807806-3"])
    razon_social: str = Field(..., examples=["CONSTRUCTORA 4M SRL"])
    condicion_iva: Optional[str] = Field(default=None, examples=["Responsable Inscripto"])

class ProveedorRead(BaseModel):
    id: str
    cuit: str
    razon_social: str
    condicion_iva: Optional[str] = None
