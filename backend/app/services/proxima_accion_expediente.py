from dataclasses import dataclass

from app.domain.estados import EstadoExpediente
from app.domain.habilitacion_proveedor_op import EstadoHabilitacionProveedorOP
from app.repositories.disposicion_repository import DisposicionRepository
from app.schemas.expediente import ExpedienteRead
from app.schemas.proxima_accion_expediente import (
    CodigoProximaAccionExpediente as Codigo,
    ProximaAccionExpedienteRead,
)


@dataclass(frozen=True)
class _Candidata:
    prioridad: int
    codigo: Codigo
    etiqueta: str
    descripcion: str
    documento_op_id: str | None = None


class ProximaAccionExpedienteService:
    """Read model derivado; no persiste estado ni consulta historial."""

    def __init__(
        self,
        expediente_service,
        documento_service,
        validacion_service,
        habilitacion_proveedor_op_service,
        disposicion_repository: DisposicionRepository,
    ) -> None:
        self._expedientes = expediente_service
        self._documentos = documento_service
        self._validaciones = validacion_service
        self._habilitaciones = habilitacion_proveedor_op_service
        self._disposiciones = disposicion_repository

    def obtener(self, expediente_id: str) -> ProximaAccionExpedienteRead:
        return self._derivar(self._expedientes.obtener(expediente_id))

    def listar(self) -> list[ProximaAccionExpedienteRead]:
        return [self._derivar(expediente) for expediente in self._expedientes.listar()]

    def _derivar(self, expediente: ExpedienteRead) -> ProximaAccionExpedienteRead:
        disposiciones = self._disposiciones.listar_por_expediente(expediente.id)
        if self._es_legacy(expediente, disposiciones):
            return self._legacy(expediente)

        estado = expediente.estado.value if hasattr(expediente.estado, "value") else str(expediente.estado)
        if estado == EstadoExpediente.ARCHIVADO.value:
            return self._respuesta(expediente.id, _Candidata(10, Codigo.CONSULTAR_HISTORIAL, "Consulta histórica", "El Expediente está archivado y permanece disponible para consulta."))
        if estado in {EstadoExpediente.CERRADO.value, EstadoExpediente.DESISTIDO.value}:
            return self._respuesta(expediente.id, _Candidata(9, Codigo.ARCHIVAR_EXPEDIENTE, "Archivar expediente", "Registrar el archivo institucional del Expediente."))
        if estado == EstadoExpediente.PENDIENTE_REVALIDACION.value:
            return self._respuesta(expediente.id, _Candidata(1, Codigo.REVALIDAR_EXPEDIENTE, "Revalidar expediente", "La validación administrativa fue invalidada y debe registrarse nuevamente."))

        documentos = self._documentos.listar_por_expediente(expediente.id)
        ops = sorted((documento for documento in documentos if documento.tipo.upper() == "OP"), key=lambda documento: documento.id)
        candidatas: list[_Candidata] = []
        disposiciones_por_op = {
            disposicion.documento_op_id: disposicion
            for disposicion in disposiciones
            if disposicion.documento_op_id is not None
        }

        for op in ops:
            habilitacion = self._habilitaciones.evaluar(expediente.id, op.id)
            estado_habilitacion = habilitacion.estado
            if estado_habilitacion == EstadoHabilitacionProveedorOP.REQUIERE_REASIGNACION_PROVEEDOR:
                candidatas.append(_Candidata(2, Codigo.REGULARIZAR_PROVEEDOR, "Regularizar proveedor", "Resolver la discrepancia entre el proveedor seleccionado y el identificado en la OP.", op.id))
            elif estado_habilitacion == EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL:
                candidatas.append(_Candidata(3, Codigo.CONTROLAR_PROVEEDOR, "Controlar proveedor", "Ejecutar el control administrativo del proveedor para la OP.", op.id))
            elif estado_habilitacion == EstadoHabilitacionProveedorOP.PROVEEDOR_NO_VERIFICABLE:
                candidatas.append(_Candidata(5, Codigo.REVISAR_DOCUMENTACION_OP, "Revisar documentación de la OP", "La OP no permite identificar confiablemente al proveedor.", op.id))
            elif estado_habilitacion == EstadoHabilitacionProveedorOP.REQUIERE_SELECCION_PROVEEDOR:
                candidatas.append(_Candidata(4, Codigo.SELECCIONAR_PROVEEDOR, "Seleccionar proveedor", "Registrar el proveedor previsto para este Expediente.", op.id))
            elif estado_habilitacion == EstadoHabilitacionProveedorOP.SIN_SOLICITUD_ASOCIADA:
                candidatas.append(_Candidata(4, Codigo.COMPLETAR_PREPARACION, "Completar preparación", "Resolver la asociación administrativa del Expediente.", op.id))
            elif estado_habilitacion == EstadoHabilitacionProveedorOP.HABILITADO:
                disposicion = disposiciones_por_op.get(op.id)
                if disposicion is None:
                    candidatas.append(_Candidata(6, Codigo.PREPARAR_DISPOSICION, "Preparar Disposición", "Generar y emitir la Disposición correspondiente a la OP.", op.id))
                elif disposicion.fecha_formalizacion is None:
                    candidatas.append(_Candidata(7, Codigo.REGISTRAR_FORMALIZACION, "Registrar formalización", "Registrar la formalización de la Disposición correspondiente a la OP.", op.id))

        if candidatas:
            elegida = min(candidatas, key=lambda candidata: (candidata.prioridad, candidata.documento_op_id or ""))
            return self._respuesta(expediente.id, elegida)

        if ops and len(disposiciones_por_op) == len(ops) and all(
            disposicion.fecha_formalizacion is not None
            for disposicion in disposiciones_por_op.values()
        ):
            return self._respuesta(expediente.id, _Candidata(8, Codigo.CERRAR_EXPEDIENTE, "Cerrar expediente", "Todas las Disposiciones de las OP están formalizadas."))

        validacion = self._validaciones.obtener_vigente(expediente.id)
        if validacion is None:
            incompleto = not all((expediente.objeto, expediente.establecimiento, expediente.solicitud_intervencion_id, expediente.decision_administrativa_id))
            if incompleto:
                return self._respuesta(expediente.id, _Candidata(1, Codigo.COMPLETAR_PREPARACION, "Completar preparación", "Completar los datos administrativos requeridos del Expediente."))
            return self._respuesta(expediente.id, _Candidata(1, Codigo.COMPLETAR_VALIDACION, "Completar validación", "Completar y registrar la validación administrativa."))

        return self._respuesta(expediente.id, _Candidata(5, Codigo.INCORPORAR_OP, "Incorporar Orden de Pago", "La validación está vigente; corresponde incorporar una Orden de Pago."))

    @staticmethod
    def _es_legacy(expediente: ExpedienteRead, disposiciones) -> bool:
        estado = expediente.estado.value if hasattr(expediente.estado, "value") else str(expediente.estado)
        return (
            estado in {EstadoExpediente.DISPOSICION_EMITIDA.value, EstadoExpediente.FIRMADO.value}
            or (estado == EstadoExpediente.ARCHIVADO.value and expediente.fecha_cierre is None and expediente.fecha_desistimiento is None)
            or any(disposicion.documento_op_id is None for disposicion in disposiciones)
        )

    def _legacy(self, expediente: ExpedienteRead) -> ProximaAccionExpedienteRead:
        estado = expediente.estado.value if hasattr(expediente.estado, "value") else str(expediente.estado)
        if estado == EstadoExpediente.DISPOSICION_EMITIDA.value:
            candidata = _Candidata(1, Codigo.REGISTRAR_FIRMA_LEGACY, "Registrar firma", "Continuar el circuito histórico de firma de la Disposición global.")
        elif estado == EstadoExpediente.FIRMADO.value:
            candidata = _Candidata(2, Codigo.ARCHIVAR_EXPEDIENTE, "Archivar expediente", "Continuar el circuito histórico de archivo.")
        else:
            candidata = _Candidata(10, Codigo.CONSULTAR_HISTORIAL, "Consulta histórica", "El Expediente pertenece al circuito histórico y es de solo lectura.")
        return self._respuesta(expediente.id, candidata, circuito_legacy=True)

    @staticmethod
    def _respuesta(expediente_id: str, candidata: _Candidata, *, circuito_legacy: bool = False) -> ProximaAccionExpedienteRead:
        return ProximaAccionExpedienteRead(
            expediente_id=expediente_id,
            codigo=candidata.codigo,
            etiqueta=candidata.etiqueta,
            descripcion=candidata.descripcion,
            prioridad=candidata.prioridad,
            documento_op_id=candidata.documento_op_id,
            circuito_legacy=circuito_legacy,
        )
