from app.domain.disposicion import Disposicion
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
# Reutilización provisional de conversores genéricos de Documento.
# Se extraerán a un módulo neutral junto con F4 en un refactor posterior.
from app.infrastructure.database.mappers.control_proveedor_op_mapper import (
    documento_id_a_secuencia,
    secuencia_a_documento_id,
)


def a_modelo(disposicion: Disposicion) -> DisposicionModel:
    return DisposicionModel(
        id_disposicion=disposicion.id_disposicion,
        expediente_id=disposicion.expediente_id,
        configuracion_uc_id=disposicion.configuracion_uc_id,
        numero_disposicion=disposicion.numero_disposicion,
        fecha_emision=disposicion.fecha_emision,
        fondo_interviniente=disposicion.fondo_interviniente,
        numero_op=disposicion.numero_op,
        numero_liquidacion=disposicion.numero_liquidacion,
        proveedor=disposicion.proveedor,
        cuit=disposicion.cuit,
        importe=disposicion.importe,
        objeto=disposicion.objeto,
        establecimiento=disposicion.establecimiento,
        valor_uc_aplicado=disposicion.valor_uc_aplicado,
        cantidad_uc=disposicion.cantidad_uc,
        procedimiento_contratacion=(
            disposicion.procedimiento_contratacion
        ),
        norma_uc=disposicion.norma_uc,
        texto_emitido=disposicion.texto_emitido,
        ruta_docx=disposicion.ruta_docx,
        documento_op_secuencia=(
            documento_id_a_secuencia(disposicion.documento_op_id)
            if disposicion.documento_op_id is not None
            else None
        ),
        control_proveedor_op_id=disposicion.control_proveedor_op_id,
        seleccion_proveedor_id=disposicion.seleccion_proveedor_id,
        proveedor_definitivo_id=disposicion.proveedor_definitivo_id,
        proveedor_definitivo_cuit=disposicion.proveedor_definitivo_cuit,
        proveedor_definitivo_razon_social=(
            disposicion.proveedor_definitivo_razon_social
        ),
    )


def a_dominio(modelo: DisposicionModel) -> Disposicion:
    return Disposicion(
        id_disposicion=modelo.id_disposicion,
        expediente_id=modelo.expediente_id,
        configuracion_uc_id=modelo.configuracion_uc_id,
        numero_disposicion=modelo.numero_disposicion,
        fecha_emision=modelo.fecha_emision,
        fondo_interviniente=modelo.fondo_interviniente,
        numero_op=modelo.numero_op,
        numero_liquidacion=modelo.numero_liquidacion,
        proveedor=modelo.proveedor,
        cuit=modelo.cuit,
        importe=modelo.importe,
        objeto=modelo.objeto,
        establecimiento=modelo.establecimiento,
        valor_uc_aplicado=modelo.valor_uc_aplicado,
        cantidad_uc=modelo.cantidad_uc,
        procedimiento_contratacion=modelo.procedimiento_contratacion,
        norma_uc=modelo.norma_uc,
        texto_emitido=modelo.texto_emitido,
        ruta_docx=modelo.ruta_docx,
        documento_op_id=(
            secuencia_a_documento_id(modelo.documento_op_secuencia)
            if modelo.documento_op_secuencia is not None
            else None
        ),
        control_proveedor_op_id=modelo.control_proveedor_op_id,
        seleccion_proveedor_id=modelo.seleccion_proveedor_id,
        proveedor_definitivo_id=modelo.proveedor_definitivo_id,
        proveedor_definitivo_cuit=modelo.proveedor_definitivo_cuit,
        proveedor_definitivo_razon_social=(
            modelo.proveedor_definitivo_razon_social
        ),
    )
