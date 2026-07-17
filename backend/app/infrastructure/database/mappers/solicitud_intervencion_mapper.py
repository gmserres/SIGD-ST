from app.domain.solicitud_intervencion import SolicitudIntervencion
from app.infrastructure.database.models.solicitud_intervencion_model import (
    SolicitudIntervencionModel,
)


def a_modelo(
    solicitud: SolicitudIntervencion,
) -> SolicitudIntervencionModel:
    return SolicitudIntervencionModel(
        id_solicitud=solicitud.id_solicitud,
        numero_solicitud=solicitud.numero_solicitud,
        procedencia=solicitud.procedencia,
        id_suna=solicitud.id_suna,
        fecha_ingreso=solicitud.fecha_ingreso,
        establecimiento=solicitud.establecimiento,
        solicitante=solicitud.solicitante,
        motivo=solicitud.motivo,
        prioridad=solicitud.prioridad,
        estado=solicitud.estado,
    )


def a_dominio(
    modelo: SolicitudIntervencionModel,
) -> SolicitudIntervencion:
    return SolicitudIntervencion(
        id_solicitud=modelo.id_solicitud,
        numero_solicitud=modelo.numero_solicitud,
        procedencia=modelo.procedencia,
        id_suna=modelo.id_suna,
        fecha_ingreso=modelo.fecha_ingreso,
        establecimiento=modelo.establecimiento,
        solicitante=modelo.solicitante,
        motivo=modelo.motivo,
        prioridad=modelo.prioridad,
        estado=modelo.estado,
    )


def actualizar_modelo(
    modelo: SolicitudIntervencionModel,
    solicitud: SolicitudIntervencion,
) -> None:
    modelo.numero_solicitud = solicitud.numero_solicitud
    modelo.procedencia = solicitud.procedencia
    modelo.id_suna = solicitud.id_suna
    modelo.fecha_ingreso = solicitud.fecha_ingreso
    modelo.establecimiento = solicitud.establecimiento
    modelo.solicitante = solicitud.solicitante
    modelo.motivo = solicitud.motivo
    modelo.prioridad = solicitud.prioridad
    modelo.estado = solicitud.estado
