from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.mappers.expediente_mapper import a_dominio
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.repositories.registrar_archivo_persistence import (
    ArchivoYaRegistradoError,
    EstadoExpedienteIncompatibleParaArchivoError,
    ExpedienteNoEncontradoAlRegistrarArchivoError,
    FechaArchivoAnteriorAFirmaError,
    FirmaAusenteOInconsistenteAlArchivarError,
)


class PostgresRegistrarArchivoPersistence:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def registrar(
        self,
        expediente_id: str,
        fecha_archivo: date,
        usuario_registro_archivo: str,
    ) -> Expediente:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(ExpedienteModel.id == expediente_id)
                    .with_for_update()
                )
                if expediente is None:
                    raise ExpedienteNoEncontradoAlRegistrarArchivoError(
                        expediente_id
                    )
                if (
                    expediente.fecha_archivo is not None
                    or expediente.usuario_registro_archivo is not None
                ):
                    raise ArchivoYaRegistradoError(expediente_id)
                if expediente.estado != EstadoExpediente.FIRMADO.value:
                    raise EstadoExpedienteIncompatibleParaArchivoError(
                        expediente_id
                    )
                if (
                    expediente.fecha_firma is None
                    or expediente.usuario_registro_firma is None
                ):
                    raise FirmaAusenteOInconsistenteAlArchivarError(
                        expediente_id
                    )
                if fecha_archivo < expediente.fecha_firma:
                    raise FechaArchivoAnteriorAFirmaError(expediente_id)

                expediente.fecha_archivo = fecha_archivo
                expediente.usuario_registro_archivo = (
                    usuario_registro_archivo
                )
                expediente.estado = EstadoExpediente.ARCHIVADO.value
                session.flush()
                actualizado = a_dominio(expediente)
                session.commit()
                return actualizado
            except Exception:
                session.rollback()
                raise
