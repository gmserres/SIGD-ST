from app.composition.decision_administrativa import decision_administrativa_repository
from app.composition.expediente import expediente_repository
from app.composition.proveedor import proveedor_repository
from app.composition.solicitud_intervencion import solicitud_intervencion_repository
from app.core.settings import get_database_url
from app.infrastructure.database.repositories.seleccion_proveedor_postgres_repository import PostgresSeleccionProveedorRepository
from app.infrastructure.database.session import crear_fabrica_sesiones, crear_motor
from app.services.seleccion_proveedor_service import SeleccionProveedorService


_engine = crear_motor(get_database_url())
_session_factory = crear_fabrica_sesiones(_engine)
seleccion_proveedor_repository = PostgresSeleccionProveedorRepository(
    _session_factory
)
seleccion_proveedor_service = SeleccionProveedorService(
    expediente_repository=expediente_repository,
    solicitud_repository=solicitud_intervencion_repository,
    decision_repository=decision_administrativa_repository,
    proveedor_repository=proveedor_repository,
    seleccion_repository=seleccion_proveedor_repository,
)
