from app.composition.control_proveedor_op import (
    control_proveedor_op_repository,
)
from app.composition.documento import documento_service
from app.composition.expediente import expediente_service
from app.composition.proveedor import proveedor_repository
from app.composition.seleccion_proveedor import (
    seleccion_proveedor_repository,
)
from app.services.evaluar_habilitacion_proveedor_op_service import (
    EvaluarHabilitacionProveedorOPService,
)


evaluar_habilitacion_proveedor_op_service = (
    EvaluarHabilitacionProveedorOPService(
        expediente_service=expediente_service,
        documento_service=documento_service,
        seleccion_repository=seleccion_proveedor_repository,
        control_repository=control_proveedor_op_repository,
        proveedor_repository=proveedor_repository,
    )
)
