from app.domain.disposicion import Disposicion
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
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
    )
