from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.estados import EstadoExpediente
from app.infrastructure.database.mappers.documento_mapper import (
    a_modelo,
    a_schema,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.persistence.validacion_vigencia import (
    MOTIVO_CARGA_OP,
    USUARIO_CAMBIO_MATERIAL,
    invalidar_modelo,
    obtener_modelo_vigente,
)
from app.schemas.documento import DocumentoCreate, DocumentoRead


class PostgresCargarOPPersistence:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(
        self,
        expediente_id: str,
        data: DocumentoCreate,
        fecha_carga: datetime,
    ) -> DocumentoRead:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(ExpedienteModel.id == expediente_id)
                    .with_for_update()
                )
                if expediente is None:
                    raise KeyError(expediente_id)

                documento = a_modelo(
                    expediente_id,
                    data,
                    fecha_carga,
                )
                session.add(documento)

                vigente = obtener_modelo_vigente(
                    session,
                    expediente_id,
                    bloquear=True,
                )
                if vigente is None:
                    expediente.estado = (
                        EstadoExpediente.DOCUMENTACION_EN_CARGA.value
                    )
                else:
                    invalidar_modelo(
                        vigente,
                        fecha=fecha_carga,
                        motivo=MOTIVO_CARGA_OP,
                        usuario=USUARIO_CAMBIO_MATERIAL,
                    )
                    expediente.estado = (
                        EstadoExpediente.PENDIENTE_REVALIDACION.value
                    )

                session.flush()
                resultado = a_schema(documento)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise
