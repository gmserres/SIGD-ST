from app.composition.expediente import session_factory
from app.infrastructure.database.repositories.checklist_fisico_postgres_repository import (
    PostgresChecklistFisicoRepository,
)
from app.infrastructure.database.persistence.actualizar_checklist_postgres import (
    PostgresActualizarChecklistPersistence,
)
from app.services.checklist_fisico import ChecklistFisicoService


checklist_fisico_repository = PostgresChecklistFisicoRepository(
    session_factory
)
actualizar_checklist_persistence = (
    PostgresActualizarChecklistPersistence(session_factory)
)
checklist_fisico_service = ChecklistFisicoService(
    checklist_fisico_repository,
    actualizar_checklist_persistence,
)
