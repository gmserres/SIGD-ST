from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.mappers.disposicion_mapper import a_modelo
from app.infrastructure.database.mappers.expediente_mapper import a_dominio
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.persistence.disposicion_conflicts import (
    traducir_integrity_error_disposicion,
    verificar_disposicion_duplicada,
)
from app.repositories.emitir_disposicion_persistence import (
    EstadoExpedienteIncompatibleError,
    ExpedienteNoEncontradoAlEmitirError,
)


class PostgresEmitirDisposicionPersistence:
    def __init__(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        self._session_factory = session_factory

    def emitir(
        self,
        disposicion: Disposicion,
        expediente_id: str,
    ) -> Expediente:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(ExpedienteModel.id == expediente_id)
                    .with_for_update()
                )
                if expediente is None:
                    raise ExpedienteNoEncontradoAlEmitirError(
                        expediente_id
                    )
                if expediente.estado != EstadoExpediente.VALIDADO.value:
                    raise EstadoExpedienteIncompatibleError(
                        expediente_id, expediente.estado
                    )

                verificar_disposicion_duplicada(session, disposicion)
                session.add(a_modelo(disposicion))
                expediente.estado = (
                    EstadoExpediente.DISPOSICION_EMITIDA.value
                )
                session.flush()
                expediente_actualizado = a_dominio(expediente)
                session.commit()
                return expediente_actualizado
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
