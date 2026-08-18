from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.infrastructure.database.mappers.control_proveedor_op_mapper import (
    documento_id_a_secuencia,
)
from app.infrastructure.database.mappers.disposicion_mapper import (
    a_dominio as disposicion_a_dominio,
    a_modelo,
)
from app.infrastructure.database.mappers.expediente_mapper import a_dominio as expediente_a_dominio
from app.infrastructure.database.models.control_proveedor_op_model import (
    ControlProveedorOPModel,
)
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.seleccion_proveedor_model import (
    SeleccionProveedorModel,
)
from app.infrastructure.database.persistence.disposicion_conflicts import (
    traducir_integrity_error_disposicion,
    verificar_disposicion_duplicada,
)
from app.repositories.emitir_disposicion_persistence import (
    ContextoEmisionObsoletoError,
    EstadoExpedienteIncompatibleError,
    ExpedienteNoEncontradoAlEmitirError,
)


class PostgresEmitirDisposicionPersistence:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def emitir(
        self,
        disposicion: Disposicion,
        expediente_id: str,
    ) -> Disposicion:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(ExpedienteModel.id == expediente_id)
                    .with_for_update()
                )
                if expediente is None:
                    raise ExpedienteNoEncontradoAlEmitirError(expediente_id)
                if expediente.estado != EstadoExpediente.VALIDADO.value:
                    raise EstadoExpedienteIncompatibleError(
                        expediente_id, expediente.estado
                    )
                if disposicion.documento_op_id is None:
                    verificar_disposicion_duplicada(session, disposicion)
                    session.add(a_modelo(disposicion))
                    expediente.estado = EstadoExpediente.DISPOSICION_EMITIDA.value
                    session.flush()
                    actualizado = expediente_a_dominio(expediente)
                    session.commit()
                    return actualizado

                documento_secuencia = documento_id_a_secuencia(
                    disposicion.documento_op_id
                )
                seleccion = session.scalar(
                    select(SeleccionProveedorModel)
                    .where(
                        SeleccionProveedorModel.id_seleccion
                        == disposicion.seleccion_proveedor_id
                    )
                    .with_for_update()
                )
                if (
                    seleccion is None
                    or not seleccion.vigente
                    or seleccion.expediente_id != expediente_id
                    or str(seleccion.solicitud_intervencion_id)
                    != str(expediente.solicitud_intervencion_id)
                    or str(seleccion.proveedor_id)
                    != disposicion.proveedor_definitivo_id
                ):
                    raise ContextoEmisionObsoletoError(
                        "La selección habilitante dejó de estar vigente."
                    )
                documento = session.scalar(
                    select(DocumentoModel)
                    .where(DocumentoModel.secuencia == documento_secuencia)
                    .with_for_update()
                )
                if (
                    documento is None
                    or documento.expediente_id != expediente_id
                    or documento.tipo.upper() != "OP"
                ):
                    raise ContextoEmisionObsoletoError(
                        "La Orden de Pago ya no corresponde al Expediente."
                    )

                control = session.scalar(
                    select(ControlProveedorOPModel)
                    .where(
                        ControlProveedorOPModel.documento_secuencia
                        == documento_secuencia
                    )
                    .order_by(ControlProveedorOPModel.secuencia.desc())
                    .limit(1)
                    .with_for_update()
                )
                if (
                    control is None
                    or str(control.id_control)
                    != disposicion.control_proveedor_op_id
                    or control.expediente_id != expediente_id
                    or str(control.solicitud_intervencion_id)
                    != str(expediente.solicitud_intervencion_id)
                    or str(control.seleccion_proveedor_id)
                    != disposicion.seleccion_proveedor_id
                    or control.estado != "COINCIDE"
                    or control.cuit_detectado
                    != disposicion.proveedor_definitivo_cuit
                    or control.razon_social_detectada
                    != disposicion.proveedor_definitivo_razon_social
                ):
                    raise ContextoEmisionObsoletoError(
                        "El control habilitante dejó de ser autoritativo."
                    )

                verificar_disposicion_duplicada(session, disposicion)
                modelo = a_modelo(disposicion)
                session.add(modelo)
                session.flush()
                guardada = disposicion_a_dominio(modelo)
                session.commit()
                return guardada
            except IntegrityError as exc:
                session.rollback()
                error_traducido = traducir_integrity_error_disposicion(
                    exc, disposicion
                )
                if error_traducido is not None:
                    raise error_traducido from exc
                raise
            except Exception:
                session.rollback()
                raise
