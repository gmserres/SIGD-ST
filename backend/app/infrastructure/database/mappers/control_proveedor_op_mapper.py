from app.domain.control_proveedor_op import EstadoControlProveedorOP
from app.domain.control_proveedor_op_evidencia import (
    ControlProveedorOPEvidencia,
)
from app.infrastructure.database.models.control_proveedor_op_model import (
    ControlProveedorOPModel,
)


def documento_id_a_secuencia(documento_op_id: str) -> int:
    prefijo = "DOC-"
    if not documento_op_id.startswith(prefijo):
        raise ValueError("Identificador de Documento OP inválido.")
    valor = documento_op_id[len(prefijo):]
    if not valor.isdigit():
        raise ValueError("Identificador de Documento OP inválido.")
    return int(valor)


def secuencia_a_documento_id(secuencia: int) -> str:
    return f"DOC-{secuencia:06d}"


def a_modelo(
    control: ControlProveedorOPEvidencia,
) -> ControlProveedorOPModel:
    return ControlProveedorOPModel(
        id_control=control.id_control,
        expediente_id=control.expediente_id,
        documento_secuencia=documento_id_a_secuencia(
            control.documento_op_id
        ),
        solicitud_intervencion_id=control.solicitud_intervencion_id,
        seleccion_proveedor_id=control.seleccion_proveedor_id,
        estado=control.estado.value,
        proveedor_cuit_seleccionado=(
            control.proveedor_cuit_seleccionado
        ),
        proveedor_razon_social_seleccionada=(
            control.proveedor_razon_social_seleccionada
        ),
        cuit_detectado=control.cuit_detectado,
        razon_social_detectada=control.razon_social_detectada,
        advertencias=list(control.advertencias),
        fecha_control=control.fecha_control,
        modo_analisis=control.modo_analisis,
    )


def a_dominio(
    modelo: ControlProveedorOPModel,
) -> ControlProveedorOPEvidencia:
    return ControlProveedorOPEvidencia(
        id_control=modelo.id_control,
        expediente_id=modelo.expediente_id,
        documento_op_id=secuencia_a_documento_id(
            modelo.documento_secuencia
        ),
        solicitud_intervencion_id=modelo.solicitud_intervencion_id,
        seleccion_proveedor_id=modelo.seleccion_proveedor_id,
        estado=EstadoControlProveedorOP(modelo.estado),
        proveedor_cuit_seleccionado=(
            modelo.proveedor_cuit_seleccionado
        ),
        proveedor_razon_social_seleccionada=(
            modelo.proveedor_razon_social_seleccionada
        ),
        cuit_detectado=modelo.cuit_detectado,
        razon_social_detectada=modelo.razon_social_detectada,
        advertencias=tuple(modelo.advertencias),
        fecha_control=modelo.fecha_control,
        modo_analisis=modelo.modo_analisis,
    )
