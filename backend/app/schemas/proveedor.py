from pydantic import BaseModel


class ProveedorCreate(BaseModel):
    cuit: str
    razon_social: str


class ProveedorUpdate(BaseModel):
    razon_social: str


class ProveedorEstadoUpdate(BaseModel):
    activo: bool


class ProveedorRead(BaseModel):
    id_proveedor: str
    cuit: str
    razon_social: str
    activo: bool
