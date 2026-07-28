from app.composition.analisis_op import analisis_op_service
from app.composition.decision_administrativa import (
    decision_administrativa_service,
)
from app.composition.expediente import expediente_service
from app.core.settings import get_database_url
from app.infrastructure.database.persistence.emitir_disposicion_postgres import (
    PostgresEmitirDisposicionPersistence,
)
from app.infrastructure.database.repositories.disposicion_postgres_repository import (
    PostgresDisposicionRepository,
)
from app.infrastructure.database.session import (
    crear_fabrica_sesiones,
    crear_motor,
)
from app.services.consulta_disposicion import ConsultaDisposicionService
from app.services.disposicion_docx import disposicion_docx_service
from app.services.disposiciones import disposicion_service
from app.services.emision_disposicion import EmisionDisposicionService
from app.services.validaciones import validacion_service


_engine = crear_motor(get_database_url())
_session_factory = crear_fabrica_sesiones(_engine)
disposicion_repository = PostgresDisposicionRepository(_session_factory)
emitir_disposicion_persistence = PostgresEmitirDisposicionPersistence(
    _session_factory
)
emision_disposicion_service = EmisionDisposicionService(
    expediente_service=expediente_service,
    decision_service=decision_administrativa_service,
    analisis_op_service=analisis_op_service,
    disposicion_service=disposicion_service,
    disposicion_docx_service=disposicion_docx_service,
    validacion_service=validacion_service,
    persistence=emitir_disposicion_persistence,
)
consulta_disposicion_service = ConsultaDisposicionService(
    disposicion_repository
)
