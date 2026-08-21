from app.composition.expediente import session_factory
from app.infrastructure.database.repositories.timeline_expediente_postgres_repository import (
    PostgresTimelineExpedienteRepository,
)
from app.services.timeline_expediente import TimelineExpedienteService


timeline_expediente_repository = PostgresTimelineExpedienteRepository(
    session_factory
)
timeline_expediente_service = TimelineExpedienteService(
    timeline_expediente_repository
)
