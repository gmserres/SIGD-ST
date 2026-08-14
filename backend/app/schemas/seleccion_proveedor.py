from datetime import datetime

from pydantic import BaseModel, field_validator


class SeleccionProveedorCreate(BaseModel):
    proveedor_id: str
    seleccionado_por: str

    @field_validator("proveedor_id", "seleccionado_por")
    @classmethod
    def validar_campo_obligatorio(cls, valor: str) -> str:
        valor_normalizado = valor.strip()
        if not valor_normalizado:
            raise ValueError("El valor es obligatorio.")
        return valor_normalizado


class ReemplazoProveedorCreate(SeleccionProveedorCreate):
    motivo_reemplazo: str

    @field_validator("motivo_reemplazo")
    @classmethod
    def validar_motivo_reemplazo(cls, valor: str) -> str:
        valor_normalizado = valor.strip()
        if not valor_normalizado:
            raise ValueError("El motivo del reemplazo es obligatorio.")
        return valor_normalizado


class SeleccionProveedorRead(BaseModel):
    id_seleccion: str
    expediente_id: str
    solicitud_intervencion_id: str
    decision_administrativa_id: str
    proveedor_id: str
    fecha_seleccion: datetime
    seleccionado_por: str
    proveedor_cuit: str
    proveedor_razon_social: str
    motivo_reemplazo: str | None
    vigente: bool
