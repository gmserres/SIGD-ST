from typing import Protocol

from app.domain.seleccion_proveedor import SeleccionProveedor


class SeleccionProveedorRepository(Protocol):
    def guardar(self, seleccion: SeleccionProveedor) -> None:
        ...

    def reemplazar(
        self,
        anterior: SeleccionProveedor,
        nueva: SeleccionProveedor,
    ) -> None:
        ...

    def obtener_por_id(
        self,
        seleccion_id: str,
    ) -> SeleccionProveedor | None:
        ...

    def obtener_vigente_por_expediente(
        self,
        expediente_id: str,
    ) -> SeleccionProveedor | None:
        ...

    def listar_por_expediente(
        self,
        expediente_id: str,
    ) -> list[SeleccionProveedor]:
        ...
