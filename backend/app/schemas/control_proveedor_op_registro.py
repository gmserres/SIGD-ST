from datetime import datetime

from app.schemas.control_proveedor_op import ControlProveedorOPRead


class ControlProveedorOPRegistroRead(ControlProveedorOPRead):
    id_control: str | None
    fecha_control: datetime | None
