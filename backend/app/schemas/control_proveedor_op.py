from enum import Enum

from pydantic import BaseModel


class EstadoControlProveedorOPAdministrativo(str, Enum):
    COINCIDE = "COINCIDE"
    CUIT_DIFERENTE = "CUIT_DIFERENTE"
    NO_VERIFICABLE = "NO_VERIFICABLE"
    SIN_PROVEEDOR_SELECCIONADO = "SIN_PROVEEDOR_SELECCIONADO"
    SIN_SOLICITUD_ASOCIADA = "SIN_SOLICITUD_ASOCIADA"


class ControlProveedorOPRead(BaseModel):
    expediente_id: str
    documento_op_id: str
    solicitud_intervencion_id: str | None
    seleccion_proveedor_id: str | None
    estado: EstadoControlProveedorOPAdministrativo
    cuit_seleccionado: str | None
    cuit_detectado: str | None
    razon_social_seleccionada: str | None
    razon_social_detectada: str | None
    advertencias: list[str]
