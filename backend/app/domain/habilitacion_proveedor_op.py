from dataclasses import dataclass
from enum import Enum


class EstadoHabilitacionProveedorOP(str, Enum):
    HABILITADO = "HABILITADO"
    REQUIERE_REASIGNACION_PROVEEDOR = (
        "REQUIERE_REASIGNACION_PROVEEDOR"
    )
    REQUIERE_SELECCION_PROVEEDOR = "REQUIERE_SELECCION_PROVEEDOR"
    REQUIERE_NUEVO_CONTROL = "REQUIERE_NUEVO_CONTROL"
    PROVEEDOR_NO_VERIFICABLE = "PROVEEDOR_NO_VERIFICABLE"
    SIN_SOLICITUD_ASOCIADA = "SIN_SOLICITUD_ASOCIADA"


@dataclass(frozen=True)
class HabilitacionProveedorOP:
    expediente_id: str
    documento_op_id: str
    estado: EstadoHabilitacionProveedorOP
    solicitud_intervencion_id: str | None
    seleccion_proveedor_id: str | None
    control_proveedor_op_id: str | None
    proveedor_definitivo_id: str | None
    proveedor_definitivo_cuit: str | None
    proveedor_definitivo_razon_social: str | None
    proveedor_op_en_maestro: bool | None
    proveedor_op_activo: bool | None
    mensaje: str
    proxima_accion: str | None
