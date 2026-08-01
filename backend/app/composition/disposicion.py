from app.composition.analisis_op import analisis_op_service
from app.composition.decision_administrativa import (
    decision_administrativa_service,
)
from app.composition.expediente import expediente_service
from app.core.settings import get_database_url
from app.core.settings import STORAGE_DIR
from app.infrastructure.database.persistence.emitir_disposicion_postgres import (
    PostgresEmitirDisposicionPersistence,
)
from app.infrastructure.database.persistence.registrar_firma_postgres import (
    PostgresRegistrarFirmaPersistence,
)
from app.infrastructure.database.repositories.disposicion_postgres_repository import (
    PostgresDisposicionRepository,
)
from app.infrastructure.database.session import (
    crear_fabrica_sesiones,
    crear_motor,
)
from app.services.consulta_disposicion import ConsultaDisposicionService
from app.services.disposicion_docx import DisposicionDocxService
from app.services.disposiciones import disposicion_service
from app.services.emision_disposicion import EmisionDisposicionService
from app.composition.validacion import validacion_service
from app.composition.documento import documento_service
from app.services.habilitacion_disposicion import (
    EvaluadorHabilitacionDisposicion,
)
from app.services.registro_firma import RegistroFirmaService


_engine = crear_motor(get_database_url())
_session_factory = crear_fabrica_sesiones(_engine)
disposicion_docx_service = DisposicionDocxService(
    export_dir=(STORAGE_DIR / "exports").resolve()
)
disposicion_repository = PostgresDisposicionRepository(_session_factory)
emitir_disposicion_persistence = PostgresEmitirDisposicionPersistence(
    _session_factory
)
registrar_firma_persistence = PostgresRegistrarFirmaPersistence(
    _session_factory
)
evaluador_habilitacion_disposicion = EvaluadorHabilitacionDisposicion(
    expediente_service=expediente_service,
    decision_service=decision_administrativa_service,
    analisis_op_service=analisis_op_service,
    documento_service=documento_service,
    validacion_service=validacion_service,
)
emision_disposicion_service = EmisionDisposicionService(
    evaluador_habilitacion=evaluador_habilitacion_disposicion,
    disposicion_service=disposicion_service,
    disposicion_docx_service=disposicion_docx_service,
    persistence=emitir_disposicion_persistence,
)
consulta_disposicion_service = ConsultaDisposicionService(
    disposicion_repository
)
registro_firma_service = RegistroFirmaService(registrar_firma_persistence)
