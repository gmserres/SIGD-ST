from app.composition.analisis_op import analisis_op_service
from app.composition.documento import documento_service
from app.composition.expediente import expediente_service
from app.composition.expediente import session_factory
from app.composition.seleccion_proveedor import (
    seleccion_proveedor_repository,
)
from app.services.control_proveedor_op_service import (
    ControlProveedorOPService,
)
from app.infrastructure.database.repositories.control_proveedor_op_postgres_repository import (
    PostgresControlProveedorOPRepository,
)
from app.services.registrar_control_proveedor_op_service import (
    RegistrarControlProveedorOPService,
)


control_proveedor_op_service = ControlProveedorOPService(
    expediente_service=expediente_service,
    documento_service=documento_service,
    seleccion_proveedor_repository=seleccion_proveedor_repository,
    analisis_op_service=analisis_op_service,
)
control_proveedor_op_repository = (
    PostgresControlProveedorOPRepository(session_factory)
)
registrar_control_proveedor_op_service = (
    RegistrarControlProveedorOPService(
        control_service=control_proveedor_op_service,
        repository=control_proveedor_op_repository,
    )
)
