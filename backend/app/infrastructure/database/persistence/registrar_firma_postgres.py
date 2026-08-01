from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.mappers.expediente_mapper import a_dominio
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.repositories.registrar_firma_persistence import (
    DisposicionEmitidaNoEncontradaAlFirmarError,
    EstadoExpedienteIncompatibleParaFirmaError,
    ExpedienteNoEncontradoAlRegistrarFirmaError,
    FechaFirmaAnteriorAEmisionError,
    FirmaYaRegistradaError,
)


class PostgresRegistrarFirmaPersistence:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def registrar(
        self,
        expediente_id: str,
        fecha_firma: date,
        usuario_registro_firma: str,
    ) -> Expediente:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(ExpedienteModel.id == expediente_id)
                    .with_for_update()
                )
                if expediente is None:
                    raise ExpedienteNoEncontradoAlRegistrarFirmaError(
                        expediente_id
                    )
                if (
                    expediente.fecha_firma is not None
                    or expediente.usuario_registro_firma is not None
                ):
                    raise FirmaYaRegistradaError(expediente_id)
                if (
                    expediente.estado
                    != EstadoExpediente.DISPOSICION_EMITIDA.value
                ):
                    raise EstadoExpedienteIncompatibleParaFirmaError(
                        expediente_id
                    )

                disposicion = session.scalar(
                    select(DisposicionModel).where(
                        DisposicionModel.expediente_id == expediente_id
                    )
                )
                if disposicion is None:
                    raise DisposicionEmitidaNoEncontradaAlFirmarError(
                        expediente_id
                    )
                if fecha_firma < disposicion.fecha_emision.date():
                    raise FechaFirmaAnteriorAEmisionError(expediente_id)

                expediente.fecha_firma = fecha_firma
                expediente.usuario_registro_firma = (
                    usuario_registro_firma
                )
                expediente.estado = EstadoExpediente.FIRMADO.value
                session.flush()
                actualizado = a_dominio(expediente)
                session.commit()
                return actualizado
            except Exception:
                session.rollback()
                raise
