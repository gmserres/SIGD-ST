from app.composition.disposicion import disposicion_repository
from app.composition.documento import documento_service
from app.composition.expediente import expediente_service
from app.composition.habilitacion_proveedor_op import (
    evaluar_habilitacion_proveedor_op_service,
)
from app.composition.validacion import validacion_service
from app.services.proxima_accion_expediente import ProximaAccionExpedienteService


proxima_accion_expediente_service = ProximaAccionExpedienteService(
    expediente_service=expediente_service,
    documento_service=documento_service,
    validacion_service=validacion_service,
    habilitacion_proveedor_op_service=evaluar_habilitacion_proveedor_op_service,
    disposicion_repository=disposicion_repository,
)
