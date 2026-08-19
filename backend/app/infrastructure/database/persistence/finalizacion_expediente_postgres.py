from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.domain.finalizacion_expediente import (
    EstadoHabilitacionCierre,
    EstadoHabilitacionDesistimiento,
)
from app.infrastructure.database.mappers.expediente_mapper import a_dominio
from app.infrastructure.database.models.disposicion_model import DisposicionModel
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.repositories.finalizacion_expediente_persistence import (
    FechaCierreAnteriorAFormalizacionError,
    FechaDesistimientoAnteriorACreacionError,
    FinalizacionExpedienteError,
)
from app.schemas.finalizacion_expediente import (
    HabilitacionCierreRead,
    HabilitacionDesistimientoRead,
    OPPendienteCierreRead,
)


ESTADOS_DESISTIBLES = frozenset({
    EstadoExpediente.BORRADOR.value,
    EstadoExpediente.DOCUMENTACION_EN_CARGA.value,
    EstadoExpediente.PENDIENTE_VALIDACION.value,
    EstadoExpediente.PENDIENTE_REVALIDACION.value,
    EstadoExpediente.VALIDADO.value,
})


class PostgresFinalizacionExpedientePersistence:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def habilitacion_cierre(self, expediente_id: str) -> HabilitacionCierreRead:
        with self._session_factory() as session:
            expediente = session.scalar(
                select(ExpedienteModel).where(ExpedienteModel.id == expediente_id)
            )
            if expediente is None:
                raise KeyError(expediente_id)
            return self._evaluar_cierre(session, expediente)

    def habilitacion_desistimiento(
        self, expediente_id: str
    ) -> HabilitacionDesistimientoRead:
        with self._session_factory() as session:
            expediente = session.scalar(
                select(ExpedienteModel).where(ExpedienteModel.id == expediente_id)
            )
            if expediente is None:
                raise KeyError(expediente_id)
            return self._evaluar_desistimiento(session, expediente)

    def cerrar(
        self,
        expediente_id: str,
        fecha: date,
        usuario: str,
        registrado_en: datetime,
    ) -> Expediente:
        with self._session_factory() as session:
            try:
                expediente = self._bloquear(session, expediente_id)
                habilitacion = self._evaluar_cierre(session, expediente)
                if not habilitacion.habilitado:
                    raise FinalizacionExpedienteError(habilitacion.mensaje)
                formalizaciones = session.scalars(
                    select(DisposicionModel.fecha_formalizacion).where(
                        DisposicionModel.expediente_id == expediente_id,
                        DisposicionModel.fecha_formalizacion.is_not(None),
                    )
                ).all()
                ultima = max(formalizaciones)
                if fecha < ultima:
                    raise FechaCierreAnteriorAFormalizacionError(
                        "La fecha de cierre no puede ser anterior a la última formalización."
                    )
                expediente.estado = EstadoExpediente.CERRADO.value
                expediente.fecha_cierre = fecha
                expediente.usuario_registro_cierre = usuario
                expediente.registrado_cierre_en = registrado_en
                session.flush()
                resultado = a_dominio(expediente)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise

    def desistir(
        self,
        expediente_id: str,
        fecha: date,
        motivo: str,
        usuario: str,
        registrado_en: datetime,
    ) -> Expediente:
        with self._session_factory() as session:
            try:
                expediente = self._bloquear(session, expediente_id)
                habilitacion = self._evaluar_desistimiento(session, expediente)
                if not habilitacion.habilitado:
                    raise FinalizacionExpedienteError(habilitacion.mensaje)
                if fecha < expediente.creado.date():
                    raise FechaDesistimientoAnteriorACreacionError(
                        "La fecha de desistimiento no puede ser anterior a la creación del Expediente."
                    )
                expediente.estado = EstadoExpediente.DESISTIDO.value
                expediente.fecha_desistimiento = fecha
                expediente.usuario_registro_desistimiento = usuario
                expediente.registrado_desistimiento_en = registrado_en
                expediente.motivo_desistimiento = motivo
                session.flush()
                resultado = a_dominio(expediente)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _bloquear(session: Session, expediente_id: str) -> ExpedienteModel:
        expediente = session.scalar(
            select(ExpedienteModel)
            .where(ExpedienteModel.id == expediente_id)
            .with_for_update()
        )
        if expediente is None:
            raise KeyError(expediente_id)
        return expediente

    @staticmethod
    def _ops(session: Session, expediente_id: str) -> list[DocumentoModel]:
        return list(session.scalars(
            select(DocumentoModel)
            .where(
                DocumentoModel.expediente_id == expediente_id,
                DocumentoModel.tipo == "OP",
            )
            .order_by(DocumentoModel.secuencia)
        ).all())

    def _evaluar_cierre(
        self, session: Session, expediente: ExpedienteModel
    ) -> HabilitacionCierreRead:
        ops = self._ops(session, expediente.id)
        disposiciones = list(session.scalars(
            select(DisposicionModel).where(
                DisposicionModel.expediente_id == expediente.id,
                DisposicionModel.documento_op_secuencia.is_not(None),
            )
        ).all())
        por_op = {d.documento_op_secuencia: d for d in disposiciones}
        pendientes: list[OPPendienteCierreRead] = []
        for op in ops:
            disposicion = por_op.get(op.secuencia)
            if disposicion is None:
                pendientes.append(OPPendienteCierreRead(
                    documento_op_id=op.id,
                    nombre_archivo=op.nombre_archivo,
                    causa="SIN_DISPOSICION",
                ))
            elif disposicion.fecha_formalizacion is None:
                pendientes.append(OPPendienteCierreRead(
                    documento_op_id=op.id,
                    nombre_archivo=op.nombre_archivo,
                    causa="DISPOSICION_SIN_FORMALIZAR",
                ))
        formalizadas = sum(d.fecha_formalizacion is not None for d in disposiciones)
        base = dict(
            cantidad_op=len(ops),
            disposiciones_emitidas=len(disposiciones),
            disposiciones_formalizadas=formalizadas,
            op_pendientes=pendientes,
        )
        if expediente.estado == EstadoExpediente.CERRADO.value:
            return HabilitacionCierreRead(estado="YA_CERRADO", habilitado=False, mensaje="El Expediente ya está cerrado.", proxima_accion="Consultar la documentación histórica.", **base)
        if expediente.estado == EstadoExpediente.DESISTIDO.value:
            return HabilitacionCierreRead(estado="YA_DESISTIDO", habilitado=False, mensaje="El Expediente fue desistido.", proxima_accion="Consultar la documentación histórica.", **base)
        if expediente.estado == EstadoExpediente.ARCHIVADO.value:
            return HabilitacionCierreRead(estado="ARCHIVADO", habilitado=False, mensaje="El Expediente está archivado.", proxima_accion="Consultar la documentación histórica.", **base)
        if expediente.estado != EstadoExpediente.VALIDADO.value:
            return HabilitacionCierreRead(estado="ESTADO_NO_APTO", habilitado=False, mensaje="El Expediente debe estar VALIDADO para cerrarse.", proxima_accion="Completar el circuito administrativo.", **base)
        if not ops:
            return HabilitacionCierreRead(estado="SIN_OP", habilitado=False, mensaje="El Expediente no posee Órdenes de Pago.", proxima_accion="Evaluar el desistimiento si la intervención no se ejecutará.", **base)
        if any(p.causa == "SIN_DISPOSICION" for p in pendientes):
            return HabilitacionCierreRead(estado="OP_SIN_DISPOSICION", habilitado=False, mensaje="Existen Órdenes de Pago sin Disposición definitiva.", proxima_accion="Emitir las Disposiciones pendientes.", **base)
        if pendientes:
            return HabilitacionCierreRead(estado="DISPOSICION_SIN_FORMALIZAR", habilitado=False, mensaje="Existen Disposiciones pendientes de formalización.", proxima_accion="Formalizar las Disposiciones pendientes.", **base)
        return HabilitacionCierreRead(estado="HABILITADO", habilitado=True, mensaje="Todas las Órdenes de Pago poseen una Disposición formalizada.", proxima_accion="Confirmar el cierre administrativo del Expediente.", **base)

    def _evaluar_desistimiento(
        self, session: Session, expediente: ExpedienteModel
    ) -> HabilitacionDesistimientoRead:
        cantidad_op = len(self._ops(session, expediente.id))
        base = {"cantidad_op": cantidad_op}
        if expediente.estado == EstadoExpediente.DESISTIDO.value:
            return HabilitacionDesistimientoRead(estado="YA_DESISTIDO", habilitado=False, mensaje="El Expediente ya fue desistido.", proxima_accion="Consultar la documentación histórica.", **base)
        if expediente.estado == EstadoExpediente.CERRADO.value:
            return HabilitacionDesistimientoRead(estado="YA_CERRADO", habilitado=False, mensaje="El Expediente ya está cerrado.", proxima_accion="Consultar la documentación histórica.", **base)
        if expediente.estado == EstadoExpediente.ARCHIVADO.value:
            return HabilitacionDesistimientoRead(estado="ARCHIVADO", habilitado=False, mensaje="El Expediente está archivado.", proxima_accion="Consultar la documentación histórica.", **base)
        if expediente.estado not in ESTADOS_DESISTIBLES:
            return HabilitacionDesistimientoRead(estado="ESTADO_NO_APTO", habilitado=False, mensaje="El estado del Expediente no permite desistimiento.", proxima_accion="Revisar el estado administrativo.", **base)
        if cantidad_op:
            return HabilitacionDesistimientoRead(estado="TIENE_OP", habilitado=False, mensaje="Un Expediente con Órdenes de Pago no puede desistirse.", proxima_accion="Completar el circuito ordinario.", **base)
        return HabilitacionDesistimientoRead(estado="HABILITADO", habilitado=True, mensaje="El Expediente no posee Órdenes de Pago y puede desistirse.", proxima_accion="Registrar fecha y motivo del desistimiento.", **base)
