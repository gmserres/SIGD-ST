from app.infrastructure.database.models.validacion_administrativa_model import (
    ValidacionAdministrativaModel,
    ValidacionControlModel,
)
from app.schemas.validacion import (
    ControlValidacionSnapshotRead,
    ValidacionAdministrativaRead,
)


def a_modelo(
    validacion: ValidacionAdministrativaRead,
) -> ValidacionAdministrativaModel:
    modelo = ValidacionAdministrativaModel(
        expediente_id=validacion.expediente_id,
        resultado=validacion.resultado,
        usuario=validacion.usuario,
        fecha_validacion=validacion.fecha_validacion,
        motivo_observacion=validacion.motivo_observacion,
        estado_expediente=validacion.estado_expediente,
        fecha_invalidacion=validacion.fecha_invalidacion,
        motivo_invalidacion=validacion.motivo_invalidacion,
        usuario_invalidacion=validacion.usuario_invalidacion,
        controles=[
            ValidacionControlModel(
                orden=control.orden,
                codigo=control.codigo,
                estado=control.estado,
                observacion=control.observacion,
            )
            for control in validacion.controles
        ],
    )
    if validacion.id is not None:
        modelo.id = validacion.id
    return modelo


def a_schema(
    modelo: ValidacionAdministrativaModel,
) -> ValidacionAdministrativaRead:
    return ValidacionAdministrativaRead(
        id=modelo.id,
        expediente_id=modelo.expediente_id,
        resultado=modelo.resultado,
        usuario=modelo.usuario,
        fecha_validacion=modelo.fecha_validacion,
        motivo_observacion=modelo.motivo_observacion,
        estado_expediente=modelo.estado_expediente,
        fecha_invalidacion=modelo.fecha_invalidacion,
        motivo_invalidacion=modelo.motivo_invalidacion,
        usuario_invalidacion=modelo.usuario_invalidacion,
        controles=[
            ControlValidacionSnapshotRead(
                orden=control.orden,
                codigo=control.codigo,
                estado=control.estado,
                observacion=control.observacion,
            )
            for control in modelo.controles
        ],
    )
