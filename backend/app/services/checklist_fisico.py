from datetime import datetime

from app.schemas.checklist_fisico import ChecklistFisicoCreate, ChecklistFisicoRead
from app.services.historial import historial_service


class ChecklistFisicoService:
    def __init__(self) -> None:
        self._items: dict[str, ChecklistFisicoRead] = {}

    def obtener(self, expediente_id: str) -> ChecklistFisicoRead | None:
        return self._items.get(expediente_id)

    def guardar(self, expediente_id: str, data: ChecklistFisicoCreate) -> ChecklistFisicoRead:
        checklist = ChecklistFisicoRead(
            expediente_id=expediente_id,
            factura=data.factura,
            remito_conformidad=data.remito_conformidad,
            cae=data.cae,
            arca=data.arca,
            arba=data.arba,
            observaciones=data.observaciones,
            usuario=data.usuario,
            fecha=datetime.now(),
        )
        self._items[expediente_id] = checklist

        acreditados: list[str] = []
        if checklist.factura:
            acreditados.append("Factura")
        if checklist.remito_conformidad:
            acreditados.append("Remito/Conformidad")
        if checklist.cae:
            acreditados.append("CAE")
        if checklist.arca:
            acreditados.append("ARCA")
        if checklist.arba:
            acreditados.append("ARBA")

        detalle = "Acreditados: " + (", ".join(acreditados) if acreditados else "sin ítems marcados")
        if checklist.observaciones:
            detalle += f" | Observaciones: {checklist.observaciones}"

        historial_service.registrar(
            expediente_id,
            "CHECKLIST_FISICO_REGISTRADO",
            usuario=checklist.usuario,
            detalle=detalle,
        )
        return checklist


checklist_fisico_service = ChecklistFisicoService()
