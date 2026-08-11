from typing import Protocol

from app.domain.control_proveedor_op_evidencia import (
    ControlProveedorOPEvidencia,
)


class ControlProveedorOPRepository(Protocol):
    def guardar(
        self,
        control: ControlProveedorOPEvidencia,
    ) -> ControlProveedorOPEvidencia:
        ...

    def obtener_por_id(
        self,
        id_control: str,
    ) -> ControlProveedorOPEvidencia | None:
        ...

    def listar_por_documento(
        self,
        documento_op_id: str,
    ) -> list[ControlProveedorOPEvidencia]:
        ...

    def obtener_ultimo_por_documento(
        self,
        documento_op_id: str,
    ) -> ControlProveedorOPEvidencia | None:
        ...
