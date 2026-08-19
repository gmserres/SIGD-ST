from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.mappers.expediente_mapper import (
    a_dominio,
)
from app.infrastructure.database.mappers.validacion_administrativa_mapper import (
    a_modelo,
    a_schema,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.persistence.validacion_vigencia import (
    MOTIVO_REEMPLAZO_VALIDACION,
    invalidar_modelo,
    obtener_modelo_vigente,
)
from app.repositories.validar_expediente_persistence import (
    ExpedienteNoEncontradoAlValidarError,
)
from app.schemas.validacion import ValidacionAdministrativaRead
from app.domain.finalizacion_expediente import (
    ESTADOS_TERMINALES_ORDINARIOS,
    ExpedienteTerminalError,
)


class PostgresValidarExpedientePersistence:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def validar(
        self,
        validacion: ValidacionAdministrativaRead,
    ) -> tuple[Expediente, ValidacionAdministrativaRead]:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(
                        ExpedienteModel.id == validacion.expediente_id
                    )
                    .with_for_update()
                )
                if expediente is None:
                    raise ExpedienteNoEncontradoAlValidarError(
                        validacion.expediente_id
                    )
                if expediente.estado in ESTADOS_TERMINALES_ORDINARIOS:
                    raise ExpedienteTerminalError(
                        validacion.expediente_id, expediente.estado
                    )

                vigente = obtener_modelo_vigente(
                    session,
                    validacion.expediente_id,
                    bloquear=True,
                )
                if vigente is not None:
                    invalidar_modelo(
                        vigente,
                        fecha=validacion.fecha_validacion,
                        motivo=MOTIVO_REEMPLAZO_VALIDACION,
                        usuario=validacion.usuario,
                    )
                modelo_validacion = a_modelo(validacion)
                session.add(modelo_validacion)
                expediente.estado = EstadoExpediente.VALIDADO.value
                session.flush()
                resultado = (
                    a_dominio(expediente),
                    a_schema(modelo_validacion),
                )
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise
