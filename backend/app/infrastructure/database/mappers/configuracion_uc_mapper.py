from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)
from app.infrastructure.database.models.configuracion_uc_model import (
    ConfiguracionUCModel,
    RangoProcedimientoUCModel,
)


def _rango_a_modelo(
    rango: RangoProcedimientoUC,
    orden: int,
) -> RangoProcedimientoUCModel:
    return RangoProcedimientoUCModel(
        id_rango=rango.id_rango,
        configuracion_uc_id=rango.configuracion_uc_id,
        limite_inferior=rango.limite_inferior,
        limite_superior=rango.limite_superior,
        limite_inferior_inclusivo=rango.limite_inferior_inclusivo,
        limite_superior_inclusivo=rango.limite_superior_inclusivo,
        procedimiento=rango.procedimiento,
        articulo=rango.articulo,
        inciso=rango.inciso,
        referencia_normativa=rango.referencia_normativa,
        orden=orden,
    )


def a_modelo(configuracion: ConfiguracionUC) -> ConfiguracionUCModel:
    return ConfiguracionUCModel(
        id_configuracion=configuracion.id_configuracion,
        fecha_inicio_vigencia=configuracion.fecha_inicio_vigencia,
        fecha_fin_vigencia=configuracion.fecha_fin_vigencia,
        valor_uc=configuracion.valor_uc,
        moneda=configuracion.moneda,
        resolucion=configuracion.resolucion,
        organismo_emisor=configuracion.organismo_emisor,
        estado=configuracion.estado,
        rangos=[
            _rango_a_modelo(rango, orden)
            for orden, rango in enumerate(configuracion.rangos)
        ],
    )


def a_dominio(modelo: ConfiguracionUCModel) -> ConfiguracionUC:
    rangos_ordenados = sorted(
        modelo.rangos,
        key=lambda rango: rango.orden,
    )
    return ConfiguracionUC(
        id_configuracion=modelo.id_configuracion,
        fecha_inicio_vigencia=modelo.fecha_inicio_vigencia,
        fecha_fin_vigencia=modelo.fecha_fin_vigencia,
        valor_uc=modelo.valor_uc,
        moneda=modelo.moneda,
        resolucion=modelo.resolucion,
        organismo_emisor=modelo.organismo_emisor,
        estado=modelo.estado,
        rangos=tuple(
            RangoProcedimientoUC(
                id_rango=rango.id_rango,
                configuracion_uc_id=rango.configuracion_uc_id,
                limite_inferior=rango.limite_inferior,
                limite_superior=rango.limite_superior,
                limite_inferior_inclusivo=(
                    rango.limite_inferior_inclusivo
                ),
                limite_superior_inclusivo=(
                    rango.limite_superior_inclusivo
                ),
                procedimiento=rango.procedimiento,
                articulo=rango.articulo,
                inciso=rango.inciso,
                referencia_normativa=rango.referencia_normativa,
            )
            for rango in rangos_ordenados
        ),
    )


def actualizar_modelo(
    modelo: ConfiguracionUCModel,
    configuracion: ConfiguracionUC,
) -> None:
    modelo.fecha_inicio_vigencia = configuracion.fecha_inicio_vigencia
    modelo.fecha_fin_vigencia = configuracion.fecha_fin_vigencia
    modelo.valor_uc = configuracion.valor_uc
    modelo.moneda = configuracion.moneda
    modelo.resolucion = configuracion.resolucion
    modelo.organismo_emisor = configuracion.organismo_emisor
    modelo.estado = configuracion.estado

    rangos_existentes = {
        rango.id_rango: rango
        for rango in modelo.rangos
    }
    rangos_actualizados: list[RangoProcedimientoUCModel] = []

    for orden, rango in enumerate(configuracion.rangos):
        rango_modelo = rangos_existentes.get(rango.id_rango)
        if rango_modelo is None:
            rango_modelo = _rango_a_modelo(rango, orden)
        else:
            rango_modelo.configuracion_uc_id = rango.configuracion_uc_id
            rango_modelo.limite_inferior = rango.limite_inferior
            rango_modelo.limite_superior = rango.limite_superior
            rango_modelo.limite_inferior_inclusivo = (
                rango.limite_inferior_inclusivo
            )
            rango_modelo.limite_superior_inclusivo = (
                rango.limite_superior_inclusivo
            )
            rango_modelo.procedimiento = rango.procedimiento
            rango_modelo.articulo = rango.articulo
            rango_modelo.inciso = rango.inciso
            rango_modelo.referencia_normativa = (
                rango.referencia_normativa
            )
            rango_modelo.orden = orden
        rangos_actualizados.append(rango_modelo)

    modelo.rangos = rangos_actualizados
