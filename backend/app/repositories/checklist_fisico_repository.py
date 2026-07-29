from typing import Protocol

from app.schemas.checklist_fisico import ChecklistFisicoRead


class ChecklistFisicoRepository(Protocol):
    def obtener_por_expediente(
        self,
        expediente_id: str,
    ) -> ChecklistFisicoRead | None:
        ...

    def guardar(
        self,
        checklist: ChecklistFisicoRead,
    ) -> ChecklistFisicoRead:
        ...
