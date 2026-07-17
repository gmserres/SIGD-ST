from app.repositories.solicitud_intervencion_in_memory_repository import (
    InMemorySolicitudIntervencionRepository,
)
from app.repositories.solicitud_intervencion_repository import (
    SolicitudIntervencionRepository,
)
from app.services.solicitud_intervencion_service import (
    SolicitudIntervencionService,
)

solicitud_intervencion_repository: SolicitudIntervencionRepository = (
    InMemorySolicitudIntervencionRepository()
)
solicitud_intervencion_service = SolicitudIntervencionService(
    solicitud_intervencion_repository,
)
