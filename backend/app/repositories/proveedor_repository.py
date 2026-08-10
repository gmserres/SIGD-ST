from typing import Protocol

from app.domain.proveedor import Proveedor


class ProveedorRepository(Protocol):
    def guardar(self, proveedor: Proveedor) -> None:
        ...

    def obtener_por_id(
        self,
        proveedor_id: str,
    ) -> Proveedor | None:
        ...

    def obtener_por_cuit(
        self,
        cuit: str,
    ) -> Proveedor | None:
        ...

    def listar(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = None,
    ) -> list[Proveedor]:
        ...
