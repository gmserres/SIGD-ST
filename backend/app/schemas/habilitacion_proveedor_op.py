from pydantic import BaseModel

from app.domain.habilitacion_proveedor_op import (
    EstadoHabilitacionProveedorOP,
)


class HabilitacionProveedorOPRead(BaseModel):
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
