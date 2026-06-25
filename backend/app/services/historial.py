from datetime import datetime
from app.schemas.historial import HistorialRead

class HistorialService:
    def __init__(self) -> None:
        self._historial: dict[str, list[HistorialRead]] = {}

    def registrar(self, expediente_id: str, accion: str, usuario: str = "sistema", detalle: str | None = None) -> HistorialRead:
        historial_id = f"HIS-{sum(len(v) for v in self._historial.values()) + 1:06d}"
        evento = HistorialRead(
            id=historial_id,
            expediente_id=expediente_id,
            accion=accion,
            usuario=usuario,
            fecha=datetime.now(),
            detalle=detalle,
        )
        self._historial.setdefault(expediente_id, []).append(evento)
        return evento

    def listar_por_expediente(self, expediente_id: str) -> list[HistorialRead]:
        return self._historial.get(expediente_id, [])

historial_service = HistorialService()
