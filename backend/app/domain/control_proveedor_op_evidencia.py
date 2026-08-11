from dataclasses import dataclass
from datetime import datetime

from app.domain.control_proveedor_op import EstadoControlProveedorOP


@dataclass(frozen=True)
class ControlProveedorOPEvidencia:
    id_control: str
    expediente_id: str
    documento_op_id: str
    solicitud_intervencion_id: str
    seleccion_proveedor_id: str
    estado: EstadoControlProveedorOP
    proveedor_cuit_seleccionado: str
    proveedor_razon_social_seleccionada: str
    cuit_detectado: str | None
    razon_social_detectada: str | None
    advertencias: tuple[str, ...]
    fecha_control: datetime
    modo_analisis: str
