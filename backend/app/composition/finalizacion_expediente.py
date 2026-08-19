from app.composition.expediente import session_factory
from app.infrastructure.database.persistence.finalizacion_expediente_postgres import (
    PostgresFinalizacionExpedientePersistence,
)
from app.services.finalizacion_expediente import FinalizacionExpedienteService


finalizacion_expediente_persistence = PostgresFinalizacionExpedientePersistence(
    session_factory
)
finalizacion_expediente_service = FinalizacionExpedienteService(
    finalizacion_expediente_persistence
)
