from app.composition.expediente import session_factory
from app.infrastructure.database.persistence.validar_expediente_postgres import (
    PostgresValidarExpedientePersistence,
)
from app.infrastructure.database.repositories.validacion_administrativa_postgres_repository import (
    PostgresValidacionAdministrativaRepository,
)
from app.services.validaciones import ValidacionService


validacion_administrativa_repository = (
    PostgresValidacionAdministrativaRepository(session_factory)
)
validar_expediente_persistence = PostgresValidarExpedientePersistence(
    session_factory
)
validacion_service = ValidacionService(
    repository=validacion_administrativa_repository,
    persistence=validar_expediente_persistence,
)
