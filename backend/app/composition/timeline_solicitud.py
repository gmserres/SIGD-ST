from app.composition.expediente import session_factory
from app.composition.timeline_expediente import timeline_expediente_service
from app.infrastructure.database.repositories.timeline_solicitud_postgres_repository import (
    PostgresTimelineSolicitudRepository,
)
from app.services.timeline_solicitud import TimelineSolicitudService


timeline_solicitud_repository = PostgresTimelineSolicitudRepository(
    session_factory
)
timeline_solicitud_service = TimelineSolicitudService(
    timeline_solicitud_repository,
    timeline_expediente_service,
)
