from datetime import datetime

from app.repositories.checklist_fisico_repository import (
    ChecklistFisicoRepository,
)
from app.repositories.actualizar_checklist_persistence import (
    ActualizarChecklistPersistence,
)
from app.schemas.checklist_fisico import ChecklistFisicoCreate, ChecklistFisicoRead
from app.services.historial import historial_service


class ChecklistFisicoService:
    def __init__(
        self,
        repository: ChecklistFisicoRepository,
        persistence: ActualizarChecklistPersistence | None = None,
    ) -> None:
        self._repository = repository
        self._persistence = persistence

    def obtener(self, expediente_id: str) -> ChecklistFisicoRead | None:
        return self._repository.obtener_por_expediente(expediente_id)

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
        if self._persistence is None:
            checklist = self._repository.guardar(checklist)
        else:
            checklist = self._persistence.guardar(checklist)

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
