from app.application.configuracion_uc.determinar_procedimiento_contratacion import (
    DeterminarProcedimientoContratacion,
)
from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ObtenerConfiguracionUCVigente,
)
from app.core.settings import get_database_url
from app.infrastructure.database.repositories.configuracion_uc_postgres_repository import (
    PostgresConfiguracionUCRepository,
)
from app.infrastructure.database.session import (
    crear_fabrica_sesiones,
    crear_motor,
)
from app.services.analisis_op import AnalisisOPService


_database_url = get_database_url()
_engine = crear_motor(_database_url)
_session_factory = crear_fabrica_sesiones(_engine)
configuracion_uc_repository = PostgresConfiguracionUCRepository(
    _session_factory
)
obtener_configuracion_uc_vigente = ObtenerConfiguracionUCVigente(
    configuracion_uc_repository
)
determinar_procedimiento_contratacion = (
    DeterminarProcedimientoContratacion(
        obtener_configuracion_uc_vigente
    )
)
analisis_op_service = AnalisisOPService(
    determinar_procedimiento_contratacion,
    configuracion_uc_repository,
)
