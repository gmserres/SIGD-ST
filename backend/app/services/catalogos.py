from app.schemas.establecimiento import EstablecimientoCreate, EstablecimientoRead
from app.schemas.proveedor import ProveedorCreate, ProveedorRead

class CatalogoService:
    def __init__(self) -> None:
        self._proveedores: dict[str, ProveedorRead] = {}
        self._establecimientos: dict[str, EstablecimientoRead] = {}

    def crear_proveedor(self, data: ProveedorCreate) -> ProveedorRead:
        proveedor_id = f"PROV-{len(self._proveedores) + 1:06d}"
        proveedor = ProveedorRead(id=proveedor_id, **data.model_dump())
        self._proveedores[proveedor_id] = proveedor
        return proveedor

    def listar_proveedores(self) -> list[ProveedorRead]:
        return list(self._proveedores.values())

    def crear_establecimiento(self, data: EstablecimientoCreate) -> EstablecimientoRead:
        establecimiento_id = f"EST-{len(self._establecimientos) + 1:06d}"
        establecimiento = EstablecimientoRead(id=establecimiento_id, **data.model_dump())
        self._establecimientos[establecimiento_id] = establecimiento
        return establecimiento

    def listar_establecimientos(self) -> list[EstablecimientoRead]:
        return list(self._establecimientos.values())

catalogo_service = CatalogoService()
