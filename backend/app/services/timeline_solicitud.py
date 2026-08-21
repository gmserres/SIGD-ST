from datetime import datetime, time

from app.repositories.timeline_solicitud_repository import (
    TimelineSolicitudRepository,
)
from app.schemas.timeline_solicitud import EventoTimelineSolicitudRead
from app.services.timeline_expediente import (
    PRIORIDAD_EVENTO,
    TimelineExpedienteService,
    clave_orden_cronologico,
)


PRIORIDAD_EVENTO_SOLICITUD = {
    "SOLICITUD_INGRESADA": 0,
    "DECISION_ADMINISTRATIVA": 5,
    **PRIORIDAD_EVENTO,
}


class SolicitudTimelineInexistenteError(LookupError):
    pass


class TimelineSolicitudService:
    def __init__(
        self,
        repository: TimelineSolicitudRepository,
        timeline_expediente_service: TimelineExpedienteService,
    ) -> None:
        self._repository = repository
        self._timeline_expediente_service = timeline_expediente_service

    def obtener(
        self,
        solicitud_id: str,
    ) -> list[EventoTimelineSolicitudRead]:
        fuentes = self._repository.obtener_fuentes(solicitud_id)
        if fuentes is None:
            raise SolicitudTimelineInexistenteError(solicitud_id)

        solicitud = fuentes.solicitud
        eventos = [
            EventoTimelineSolicitudRead(
                nivel="SOLICITUD",
                solicitud_id=solicitud_id,
                expediente_id=None,
                tipo="SOLICITUD_INGRESADA",
                fecha_hora=datetime.combine(
                    solicitud.fecha_ingreso,
                    time.min,
                ),
                precision_temporal="DIA",
                titulo="Solicitud ingresada",
                entidad_origen="SOLICITUD_INTERVENCION",
                entidad_origen_id=solicitud.id_solicitud,
            )
        ]

        for decision in fuentes.decisiones:
            descripcion = (
                f"{decision.resultado}. Autoridad: "
                f"{decision.autoridad_decisora}. "
                f"Fundamento: {decision.fundamento}"
            )
            eventos.append(
                EventoTimelineSolicitudRead(
                    nivel="SOLICITUD",
                    solicitud_id=solicitud_id,
                    expediente_id=None,
                    tipo="DECISION_ADMINISTRATIVA",
                    fecha_hora=datetime.combine(
                        decision.fecha_decision,
                        time.min,
                    ),
                    precision_temporal="DIA",
                    titulo="Decisión administrativa registrada",
                    descripcion=descripcion,
                    usuario=decision.usuario_registrante,
                    entidad_origen="DECISION_ADMINISTRATIVA",
                    entidad_origen_id=decision.id_decision,
                    metadatos={
                        "resultado": decision.resultado,
                        "autoridad": decision.autoridad_decisora,
                        "fondo_interviniente": (
                            decision.fondo_interviniente
                        ),
                        "descripcion_fondo": decision.descripcion_fondo,
                    },
                )
            )

        for expediente in fuentes.expedientes:
            for evento in self._timeline_expediente_service.obtener(
                expediente.id
            ):
                precision = (
                    "DIA"
                    if evento.metadatos.get("precision_fecha") == "DIA"
                    else "FECHA_HORA"
                )
                metadatos = dict(evento.metadatos)
                metadatos.update(
                    {
                        "expediente_numero_interno": (
                            expediente.numero_interno
                        ),
                        "expediente_numero_gdeba": (
                            expediente.numero_gdeba
                        ),
                        "expediente_estado_actual": expediente.estado,
                    }
                )
                eventos.append(
                    EventoTimelineSolicitudRead(
                        nivel="EXPEDIENTE",
                        solicitud_id=solicitud_id,
                        expediente_id=expediente.id,
                        tipo=evento.tipo,
                        fecha_hora=evento.fecha_hora,
                        precision_temporal=precision,
                        titulo=evento.titulo,
                        descripcion=evento.descripcion,
                        usuario=evento.usuario,
                        entidad_origen=evento.entidad_origen,
                        entidad_origen_id=evento.entidad_origen_id,
                        documento_op_id=evento.documento_op_id,
                        metadatos=metadatos,
                    )
                )

        return sorted(eventos, key=self._clave_orden)

    @staticmethod
    def _clave_orden(evento: EventoTimelineSolicitudRead):
        # La Solicitud es antecedente necesario de todo Expediente asociado.
        # Cuando comparten fecha, esa relación durable permite ubicar su
        # ingreso antes de las actuaciones horarias sin inventar una hora.
        precision_diaria = evento.precision_temporal == "DIA"
        if evento.tipo == "SOLICITUD_INGRESADA":
            precision_diaria = False
        return clave_orden_cronologico(
            fecha_hora=evento.fecha_hora,
            precision_diaria=precision_diaria,
            prioridad=PRIORIDAD_EVENTO_SOLICITUD[evento.tipo],
            entidad_origen=evento.entidad_origen,
            entidad_origen_id=evento.entidad_origen_id,
        )
