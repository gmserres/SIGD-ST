from app.composition.disposicion import _session_factory
from app.infrastructure.database.persistence.formalizacion_disposicion_postgres import (
    PostgresFormalizacionDisposicionPersistence,
)
from app.services.formalizacion_disposicion import (
    FormalizacionDisposicionService,
)


formalizacion_disposicion_persistence = (
    PostgresFormalizacionDisposicionPersistence(_session_factory)
)
formalizacion_disposicion_service = FormalizacionDisposicionService(
    formalizacion_disposicion_persistence
)
