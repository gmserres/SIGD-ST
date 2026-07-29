from typing import Protocol

from app.schemas.checklist_fisico import ChecklistFisicoRead


class ActualizarChecklistPersistence(Protocol):
    def guardar(
        self,
        checklist: ChecklistFisicoRead,
    ) -> ChecklistFisicoRead:
        ...
