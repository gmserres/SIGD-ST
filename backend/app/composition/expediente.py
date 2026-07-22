from app.core.settings import get_database_url
from app.infrastructure.database.repositories.expediente_postgres_repository import (
    PostgresExpedienteRepository,
)
from app.infrastructure.database.session import crear_fabrica_sesiones, crear_motor
from app.services.expedientes import ExpedienteService


_engine = crear_motor(get_database_url())
_session_factory = crear_fabrica_sesiones(_engine)
expediente_repository = PostgresExpedienteRepository(_session_factory)
expediente_service = ExpedienteService(expediente_repository)
