from app.core.settings import get_database_url
from app.infrastructure.database.repositories.solicitud_intervencion_postgres_repository import (
    PostgresSolicitudIntervencionRepository,
)
from app.infrastructure.database.session import (
    crear_fabrica_sesiones,
    crear_motor,
)
from app.repositories.solicitud_intervencion_in_memory_repository import (
    InMemorySolicitudIntervencionRepository,
)
from app.repositories.solicitud_intervencion_repository import (
    SolicitudIntervencionRepository,
)
from app.services.solicitud_intervencion_service import (
    SolicitudIntervencionService,
)

_database_url = get_database_url()

solicitud_intervencion_repository: SolicitudIntervencionRepository
if _database_url:
    _engine = crear_motor(_database_url)
    _session_factory = crear_fabrica_sesiones(_engine)
    solicitud_intervencion_repository = (
        PostgresSolicitudIntervencionRepository(_session_factory)
    )
else:
    solicitud_intervencion_repository = (
        InMemorySolicitudIntervencionRepository()
    )

solicitud_intervencion_service = SolicitudIntervencionService(
    solicitud_intervencion_repository,
)
