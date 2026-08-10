from app.schemas.establecimiento import EstablecimientoCreate, EstablecimientoRead

class CatalogoService:
    def __init__(self) -> None:
        self._establecimientos: dict[str, EstablecimientoRead] = {}

    def crear_establecimiento(self, data: EstablecimientoCreate) -> EstablecimientoRead:
        establecimiento_id = f"EST-{len(self._establecimientos) + 1:06d}"
        establecimiento = EstablecimientoRead(id=establecimiento_id, **data.model_dump())
        self._establecimientos[establecimiento_id] = establecimiento
        return establecimiento

    def listar_establecimientos(self) -> list[EstablecimientoRead]:
        return list(self._establecimientos.values())

catalogo_service = CatalogoService()
