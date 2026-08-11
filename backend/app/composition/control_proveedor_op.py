from app.composition.analisis_op import analisis_op_service
from app.composition.documento import documento_service
from app.composition.expediente import expediente_service
from app.composition.seleccion_proveedor import (
    seleccion_proveedor_repository,
)
from app.services.control_proveedor_op_service import (
    ControlProveedorOPService,
)


control_proveedor_op_service = ControlProveedorOPService(
    expediente_service=expediente_service,
    documento_service=documento_service,
    seleccion_proveedor_repository=seleccion_proveedor_repository,
    analisis_op_service=analisis_op_service,
)
