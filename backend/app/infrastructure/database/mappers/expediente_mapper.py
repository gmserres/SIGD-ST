from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.models.expediente_model import ExpedienteModel


def a_modelo(expediente: Expediente) -> ExpedienteModel:
    return ExpedienteModel(
        id=expediente.id,
        numero_interno=expediente.numero_interno,
        numero_gdeba=expediente.numero_gdeba,
        solicitud_intervencion_id=expediente.solicitud_intervencion_id,
        decision_administrativa_id=expediente.decision_administrativa_id,
        configuracion_uc_id=expediente.configuracion_uc_id,
        id_suna=expediente.id_suna,
        tipo_tramite=expediente.tipo_tramite,
        estado=expediente.estado.value,
        establecimiento=expediente.establecimiento,
        objeto=expediente.objeto,
        numero_disposicion=expediente.numero_disposicion,
        creado=expediente.creado,
        fecha_firma=expediente.fecha_firma,
        usuario_registro_firma=expediente.usuario_registro_firma,
        fecha_archivo=expediente.fecha_archivo,
        usuario_registro_archivo=expediente.usuario_registro_archivo,
        fecha_cierre=expediente.fecha_cierre,
        usuario_registro_cierre=expediente.usuario_registro_cierre,
        registrado_cierre_en=expediente.registrado_cierre_en,
        fecha_desistimiento=expediente.fecha_desistimiento,
        usuario_registro_desistimiento=expediente.usuario_registro_desistimiento,
        registrado_desistimiento_en=expediente.registrado_desistimiento_en,
        motivo_desistimiento=expediente.motivo_desistimiento,
    )


def a_dominio(modelo: ExpedienteModel) -> Expediente:
    return Expediente(
        id=modelo.id,
        numero_interno=modelo.numero_interno,
        numero_gdeba=modelo.numero_gdeba,
        solicitud_intervencion_id=modelo.solicitud_intervencion_id,
        decision_administrativa_id=modelo.decision_administrativa_id,
        configuracion_uc_id=modelo.configuracion_uc_id,
        id_suna=modelo.id_suna,
        tipo_tramite=modelo.tipo_tramite,
        estado=EstadoExpediente(modelo.estado),
        establecimiento=modelo.establecimiento,
        objeto=modelo.objeto,
        numero_disposicion=modelo.numero_disposicion,
        creado=modelo.creado,
        fecha_firma=modelo.fecha_firma,
        usuario_registro_firma=modelo.usuario_registro_firma,
        fecha_archivo=modelo.fecha_archivo,
        usuario_registro_archivo=modelo.usuario_registro_archivo,
        fecha_cierre=modelo.fecha_cierre,
        usuario_registro_cierre=modelo.usuario_registro_cierre,
        registrado_cierre_en=modelo.registrado_cierre_en,
        fecha_desistimiento=modelo.fecha_desistimiento,
        usuario_registro_desistimiento=modelo.usuario_registro_desistimiento,
        registrado_desistimiento_en=modelo.registrado_desistimiento_en,
        motivo_desistimiento=modelo.motivo_desistimiento,
    )


def actualizar_modelo(modelo: ExpedienteModel, expediente: Expediente) -> None:
    modelo.numero_interno = expediente.numero_interno
    modelo.numero_gdeba = expediente.numero_gdeba
    modelo.solicitud_intervencion_id = expediente.solicitud_intervencion_id
    modelo.decision_administrativa_id = expediente.decision_administrativa_id
    modelo.configuracion_uc_id = expediente.configuracion_uc_id
    modelo.id_suna = expediente.id_suna
    modelo.tipo_tramite = expediente.tipo_tramite
    modelo.estado = expediente.estado.value
    modelo.establecimiento = expediente.establecimiento
    modelo.objeto = expediente.objeto
    modelo.numero_disposicion = expediente.numero_disposicion
    modelo.creado = expediente.creado
    modelo.fecha_firma = expediente.fecha_firma
    modelo.usuario_registro_firma = expediente.usuario_registro_firma
    modelo.fecha_archivo = expediente.fecha_archivo
    modelo.usuario_registro_archivo = expediente.usuario_registro_archivo
    modelo.fecha_cierre = expediente.fecha_cierre
    modelo.usuario_registro_cierre = expediente.usuario_registro_cierre
    modelo.registrado_cierre_en = expediente.registrado_cierre_en
    modelo.fecha_desistimiento = expediente.fecha_desistimiento
    modelo.usuario_registro_desistimiento = expediente.usuario_registro_desistimiento
    modelo.registrado_desistimiento_en = expediente.registrado_desistimiento_en
    modelo.motivo_desistimiento = expediente.motivo_desistimiento
