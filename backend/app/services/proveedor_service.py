from dataclasses import asdict
from uuid import uuid4

from app.domain.proveedor import (
    CuitProveedorDuplicadoError,
    Proveedor,
)
from app.repositories.proveedor_repository import ProveedorRepository
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorEstadoUpdate,
    ProveedorRead,
    ProveedorUpdate,
)


class ProveedorService:
    def __init__(self, repository: ProveedorRepository) -> None:
        self._repository = repository

    def registrar(self, data: ProveedorCreate) -> ProveedorRead:
        proveedor = Proveedor(
            id_proveedor=str(uuid4()),
            cuit=data.cuit,
            razon_social=data.razon_social,
        )
        if self._repository.obtener_por_cuit(proveedor.cuit) is not None:
            raise CuitProveedorDuplicadoError(
                "Ya existe un proveedor registrado con ese CUIT."
            )
        self._repository.guardar(proveedor)
        return self._a_read(proveedor)

    def obtener_por_id(self, proveedor_id: str) -> ProveedorRead:
        proveedor = self._repository.obtener_por_id(proveedor_id)
        if proveedor is None:
            raise KeyError(proveedor_id)
        return self._a_read(proveedor)

    def obtener_por_cuit(self, cuit: str) -> ProveedorRead:
        proveedor = self._repository.obtener_por_cuit(cuit)
        if proveedor is None:
            raise KeyError(cuit)
        return self._a_read(proveedor)

    def listar(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = None,
    ) -> list[ProveedorRead]:
        return [
            self._a_read(proveedor)
            for proveedor in self._repository.listar(
                buscar=buscar,
                activo=activo,
            )
        ]

    def modificar_razon_social(
        self,
        proveedor_id: str,
        data: ProveedorUpdate,
    ) -> ProveedorRead:
        proveedor = self._obtener_dominio(proveedor_id)
        actualizado = proveedor.modificar_razon_social(
            data.razon_social
        )
        self._repository.guardar(actualizado)
        return self._a_read(actualizado)

    def actualizar_estado(
        self,
        proveedor_id: str,
        data: ProveedorEstadoUpdate,
    ) -> ProveedorRead:
        proveedor = self._obtener_dominio(proveedor_id)
        actualizado = (
            proveedor.activar()
            if data.activo
            else proveedor.inactivar()
        )
        self._repository.guardar(actualizado)
        return self._a_read(actualizado)

    def _obtener_dominio(self, proveedor_id: str) -> Proveedor:
        proveedor = self._repository.obtener_por_id(proveedor_id)
        if proveedor is None:
            raise KeyError(proveedor_id)
        return proveedor

    @staticmethod
    def _a_read(proveedor: Proveedor) -> ProveedorRead:
        return ProveedorRead(**asdict(proveedor))
