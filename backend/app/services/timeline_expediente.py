from datetime import date, datetime, time

from app.repositories.timeline_expediente_repository import (
    FuentesTimelineExpediente,
    TimelineExpedienteRepository,
)
from app.schemas.timeline_expediente import EventoTimelineExpedienteRead


PRIORIDAD_EVENTO = {
    "EXPEDIENTE_CREADO": 10,
    "DOCUMENTO_INCORPORADO": 20,
    "OP_INCORPORADA": 21,
    "CHECKLIST_FISICO_REGISTRADO": 30,
    "VALIDACION_ADMINISTRATIVA": 40,
    "VALIDACION_ADMINISTRATIVA_INVALIDADA": 41,
    "PROVEEDOR_SELECCIONADO": 50,
    "PROVEEDOR_REEMPLAZADO": 51,
    "CONTROL_PROVEEDOR_OP": 60,
    "DISPOSICION_EMITIDA": 70,
    "DISPOSICION_FORMALIZADA": 71,
    "EXPEDIENTE_CERRADO": 80,
    "EXPEDIENTE_DESISTIDO": 81,
    "EXPEDIENTE_ARCHIVADO": 90,
}


def clave_orden_cronologico(
    *,
    fecha_hora: datetime,
    precision_diaria: bool,
    prioridad: int,
    entidad_origen: str,
    entidad_origen_id: str,
):
    return (
        fecha_hora.date(),
        1 if precision_diaria else 0,
        fecha_hora.time(),
        prioridad,
        entidad_origen,
        entidad_origen_id,
    )


class ExpedienteTimelineInexistenteError(LookupError):
    pass


class TimelineExpedienteService:
    def __init__(self, repository: TimelineExpedienteRepository) -> None:
        self._repository = repository

    def obtener(
        self,
        expediente_id: str,
    ) -> list[EventoTimelineExpedienteRead]:
        fuentes = self._repository.obtener_fuentes(expediente_id)
        if fuentes is None:
            raise ExpedienteTimelineInexistenteError(expediente_id)
        eventos = self._reconstruir(fuentes)
        return sorted(eventos, key=self._clave_orden)

    def _reconstruir(
        self,
        fuentes: FuentesTimelineExpediente,
    ) -> list[EventoTimelineExpedienteRead]:
        expediente = fuentes.expediente
        eventos = [
            EventoTimelineExpedienteRead(
                tipo="EXPEDIENTE_CREADO",
                fecha_hora=expediente.creado,
                titulo="Expediente creado",
                descripcion=expediente.numero_interno,
                entidad_origen="EXPEDIENTE",
                entidad_origen_id=expediente.id,
            )
        ]

        for documento in fuentes.documentos:
            es_op = documento.tipo.upper() == "OP"
            documento_id = self._documento_id(documento.secuencia)
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo=(
                        "OP_INCORPORADA"
                        if es_op
                        else "DOCUMENTO_INCORPORADO"
                    ),
                    fecha_hora=documento.fecha_carga,
                    titulo=(
                        "Orden de Pago incorporada"
                        if es_op
                        else "Documento incorporado"
                    ),
                    descripcion=documento.nombre_archivo,
                    entidad_origen="DOCUMENTO",
                    entidad_origen_id=documento_id,
                    documento_op_id=documento_id if es_op else None,
                    metadatos={"tipo_documento": documento.tipo},
                )
            )

        if fuentes.checklist is not None:
            checklist = fuentes.checklist
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="CHECKLIST_FISICO_REGISTRADO",
                    fecha_hora=checklist.fecha_registro,
                    titulo="Checklist físico registrado",
                    descripcion=checklist.observaciones,
                    usuario=checklist.usuario,
                    entidad_origen="CHECKLIST_FISICO",
                    entidad_origen_id=str(checklist.id),
                    metadatos={
                        "factura": checklist.factura,
                        "remito_conformidad": checklist.remito_conformidad,
                        "cae": checklist.cae,
                        "arca": checklist.arca,
                        "arba": checklist.arba,
                    },
                )
            )

        for validacion in fuentes.validaciones:
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="VALIDACION_ADMINISTRATIVA",
                    fecha_hora=validacion.fecha_validacion,
                    titulo="Validación administrativa",
                    descripcion=(
                        validacion.motivo_observacion
                        or validacion.resultado.replace("_", " ").title()
                    ),
                    usuario=validacion.usuario,
                    entidad_origen="VALIDACION_ADMINISTRATIVA",
                    entidad_origen_id=str(validacion.id),
                    metadatos={
                        "resultado": validacion.resultado,
                        "vigente": validacion.fecha_invalidacion is None,
                    },
                )
            )
            if validacion.fecha_invalidacion is not None:
                eventos.append(
                    EventoTimelineExpedienteRead(
                        tipo="VALIDACION_ADMINISTRATIVA_INVALIDADA",
                        fecha_hora=validacion.fecha_invalidacion,
                        titulo="Validación administrativa invalidada",
                        descripcion=validacion.motivo_invalidacion,
                        usuario=validacion.usuario_invalidacion,
                        entidad_origen="VALIDACION_ADMINISTRATIVA",
                        entidad_origen_id=str(validacion.id),
                    )
                )

        seleccion_anterior = None
        for seleccion in fuentes.selecciones:
            reemplazo = seleccion.motivo_reemplazo is not None
            descripcion = (
                f"{seleccion.proveedor_razon_social} — CUIT "
                f"{seleccion.proveedor_cuit}"
            )
            metadatos: dict[str, str | bool | None] = {
                "proveedor_id": seleccion.proveedor_id,
                "proveedor_cuit": seleccion.proveedor_cuit,
                "proveedor_razon_social": (
                    seleccion.proveedor_razon_social
                ),
                "vigente": seleccion.vigente,
                "motivo_reemplazo": seleccion.motivo_reemplazo,
            }
            if reemplazo and seleccion_anterior is not None:
                metadatos["proveedor_anterior"] = (
                    seleccion_anterior.proveedor_razon_social
                )
                descripcion += (
                    ". Reemplazó a "
                    f"{seleccion_anterior.proveedor_razon_social}: "
                    f"{seleccion.motivo_reemplazo}"
                )
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo=(
                        "PROVEEDOR_REEMPLAZADO"
                        if reemplazo
                        else "PROVEEDOR_SELECCIONADO"
                    ),
                    fecha_hora=seleccion.fecha_seleccion,
                    titulo=(
                        "Proveedor reemplazado"
                        if reemplazo
                        else "Proveedor seleccionado"
                    ),
                    descripcion=descripcion,
                    usuario=seleccion.seleccionado_por,
                    entidad_origen="SELECCION_PROVEEDOR",
                    entidad_origen_id=seleccion.id_seleccion,
                    metadatos=metadatos,
                )
            )
            seleccion_anterior = seleccion

        for control in fuentes.controles:
            documento_op_id = self._documento_id(
                control.documento_secuencia
            )
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="CONTROL_PROVEEDOR_OP",
                    fecha_hora=control.fecha_control,
                    titulo="Control Proveedor ↔ OP",
                    descripcion=(
                        f"{control.estado}. Seleccionado: "
                        f"{control.proveedor_razon_social_seleccionada}. "
                        "Detectado en OP: "
                        f"{control.razon_social_detectada or 'no informado'}."
                    ),
                    entidad_origen="CONTROL_PROVEEDOR_OP",
                    entidad_origen_id=control.id_control,
                    documento_op_id=documento_op_id,
                    metadatos={
                        "resultado": control.estado,
                        "seleccion_proveedor_id": (
                            control.seleccion_proveedor_id
                        ),
                        "cuit_seleccionado": (
                            control.proveedor_cuit_seleccionado
                        ),
                        "cuit_detectado": control.cuit_detectado,
                    },
                )
            )

        for disposicion in fuentes.disposiciones:
            documento_op_id = (
                self._documento_id(disposicion.documento_op_secuencia)
                if disposicion.documento_op_secuencia is not None
                else None
            )
            legacy = documento_op_id is None
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="DISPOSICION_EMITIDA",
                    fecha_hora=disposicion.fecha_emision,
                    titulo=(
                        "Disposición histórica emitida"
                        if legacy
                        else "Disposición emitida"
                    ),
                    descripcion=(
                        f"N.º {disposicion.numero_disposicion} — "
                        f"{disposicion.proveedor}"
                    ),
                    entidad_origen="DISPOSICION",
                    entidad_origen_id=disposicion.id_disposicion,
                    documento_op_id=documento_op_id,
                    metadatos={
                        "numero_disposicion": (
                            disposicion.numero_disposicion
                        ),
                        "numero_op": disposicion.numero_op,
                        "legacy": legacy,
                    },
                )
            )
            if disposicion.registrado_formalizacion_en is not None:
                eventos.append(
                    EventoTimelineExpedienteRead(
                        tipo="DISPOSICION_FORMALIZADA",
                        fecha_hora=(
                            disposicion.registrado_formalizacion_en
                        ),
                        titulo="Disposición formalizada",
                        descripcion=(
                            f"N.º {disposicion.numero_disposicion}"
                        ),
                        usuario=(
                            disposicion.usuario_registro_formalizacion
                        ),
                        entidad_origen="DISPOSICION",
                        entidad_origen_id=disposicion.id_disposicion,
                        documento_op_id=documento_op_id,
                    )
                )

        formalizaciones_persistidas = any(
            disposicion.registrado_formalizacion_en is not None
            for disposicion in fuentes.disposiciones
        )
        if (
            expediente.fecha_firma is not None
            and not formalizaciones_persistidas
            and len(fuentes.disposiciones) == 1
        ):
            disposicion = fuentes.disposiciones[0]
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="DISPOSICION_FORMALIZADA",
                    fecha_hora=self._fecha_como_datetime(
                        expediente.fecha_firma
                    ),
                    titulo="Formalización histórica registrada",
                    descripcion=f"N.º {disposicion.numero_disposicion}",
                    usuario=expediente.usuario_registro_firma,
                    entidad_origen="DISPOSICION",
                    entidad_origen_id=disposicion.id_disposicion,
                    metadatos={
                        "legacy": True,
                        "precision_fecha": "DIA",
                    },
                )
            )

        self._agregar_finalizacion(eventos, fuentes)
        return eventos

    def _agregar_finalizacion(
        self,
        eventos: list[EventoTimelineExpedienteRead],
        fuentes: FuentesTimelineExpediente,
    ) -> None:
        expediente = fuentes.expediente
        if expediente.registrado_cierre_en is not None:
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="EXPEDIENTE_CERRADO",
                    fecha_hora=expediente.registrado_cierre_en,
                    titulo="Expediente cerrado",
                    usuario=expediente.usuario_registro_cierre,
                    entidad_origen="EXPEDIENTE",
                    entidad_origen_id=expediente.id,
                )
            )
        if expediente.registrado_desistimiento_en is not None:
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="EXPEDIENTE_DESISTIDO",
                    fecha_hora=expediente.registrado_desistimiento_en,
                    titulo="Expediente desistido",
                    descripcion=expediente.motivo_desistimiento,
                    usuario=expediente.usuario_registro_desistimiento,
                    entidad_origen="EXPEDIENTE",
                    entidad_origen_id=expediente.id,
                )
            )
        if expediente.fecha_archivo is not None:
            if expediente.fecha_cierre is not None:
                procedencia = "CERRADO"
            elif expediente.fecha_desistimiento is not None:
                procedencia = "DESISTIDO"
            else:
                procedencia = "LEGACY_NO_DETERMINADA"
            eventos.append(
                EventoTimelineExpedienteRead(
                    tipo="EXPEDIENTE_ARCHIVADO",
                    fecha_hora=self._fecha_como_datetime(
                        expediente.fecha_archivo
                    ),
                    titulo="Expediente archivado",
                    descripcion=(
                        "Archivo histórico; la procedencia no consta."
                        if procedencia == "LEGACY_NO_DETERMINADA"
                        else f"Procedencia: {procedencia}."
                    ),
                    usuario=expediente.usuario_registro_archivo,
                    entidad_origen="EXPEDIENTE",
                    entidad_origen_id=expediente.id,
                    metadatos={
                        "procedencia": procedencia,
                        "precision_fecha": "DIA",
                    },
                )
            )

    @staticmethod
    def _fecha_como_datetime(valor: date) -> datetime:
        return datetime.combine(valor, time.min)

    @staticmethod
    def _documento_id(secuencia: int) -> str:
        return f"DOC-{secuencia:06d}"

    @staticmethod
    def _clave_orden(evento: EventoTimelineExpedienteRead):
        fecha_sin_hora = evento.metadatos.get("precision_fecha") == "DIA"
        return clave_orden_cronologico(
            fecha_hora=evento.fecha_hora,
            precision_diaria=fecha_sin_hora,
            prioridad=PRIORIDAD_EVENTO[evento.tipo],
            entidad_origen=evento.entidad_origen,
            entidad_origen_id=evento.entidad_origen_id,
        )
