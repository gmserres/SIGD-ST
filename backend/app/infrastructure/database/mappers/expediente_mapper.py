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
        id_suna=expediente.id_suna,
        tipo_tramite=expediente.tipo_tramite,
        estado=expediente.estado.value,
        establecimiento=expediente.establecimiento,
        objeto=expediente.objeto,
        numero_disposicion=expediente.numero_disposicion,
        creado=expediente.creado,
    )


def a_dominio(modelo: ExpedienteModel) -> Expediente:
    return Expediente(
        id=modelo.id,
        numero_interno=modelo.numero_interno,
        numero_gdeba=modelo.numero_gdeba,
        solicitud_intervencion_id=modelo.solicitud_intervencion_id,
        decision_administrativa_id=modelo.decision_administrativa_id,
        id_suna=modelo.id_suna,
        tipo_tramite=modelo.tipo_tramite,
        estado=EstadoExpediente(modelo.estado),
        establecimiento=modelo.establecimiento,
        objeto=modelo.objeto,
        numero_disposicion=modelo.numero_disposicion,
        creado=modelo.creado,
    )


def actualizar_modelo(modelo: ExpedienteModel, expediente: Expediente) -> None:
    modelo.numero_interno = expediente.numero_interno
    modelo.numero_gdeba = expediente.numero_gdeba
    modelo.solicitud_intervencion_id = expediente.solicitud_intervencion_id
    modelo.decision_administrativa_id = expediente.decision_administrativa_id
    modelo.id_suna = expediente.id_suna
    modelo.tipo_tramite = expediente.tipo_tramite
    modelo.estado = expediente.estado.value
    modelo.establecimiento = expediente.establecimiento
    modelo.objeto = expediente.objeto
    modelo.numero_disposicion = expediente.numero_disposicion
    modelo.creado = expediente.creado
