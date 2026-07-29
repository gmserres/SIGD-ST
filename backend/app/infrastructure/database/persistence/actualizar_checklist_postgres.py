from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.estados import EstadoExpediente
from app.infrastructure.database.mappers.checklist_fisico_mapper import (
    a_modelo,
    a_schema,
    actualizar_modelo,
)
from app.infrastructure.database.models.checklist_fisico_model import (
    ChecklistFisicoModel,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.persistence.validacion_vigencia import (
    MOTIVO_CAMBIO_CHECKLIST,
    invalidar_modelo,
    obtener_modelo_vigente,
)
from app.schemas.checklist_fisico import ChecklistFisicoRead


class PostgresActualizarChecklistPersistence:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(
        self,
        checklist: ChecklistFisicoRead,
    ) -> ChecklistFisicoRead:
        with self._session_factory() as session:
            try:
                expediente = session.scalar(
                    select(ExpedienteModel)
                    .where(
                        ExpedienteModel.id == checklist.expediente_id
                    )
                    .with_for_update()
                )
                if expediente is None:
                    raise KeyError(checklist.expediente_id)

                modelo = session.scalar(
                    select(ChecklistFisicoModel).where(
                        ChecklistFisicoModel.expediente_id
                        == checklist.expediente_id
                    )
                )
                if modelo is None:
                    modelo = a_modelo(checklist)
                    session.add(modelo)
                else:
                    actualizar_modelo(modelo, checklist)

                vigente = obtener_modelo_vigente(
                    session,
                    checklist.expediente_id,
                    bloquear=True,
                )
                if vigente is not None:
                    invalidar_modelo(
                        vigente,
                        fecha=checklist.fecha,
                        motivo=MOTIVO_CAMBIO_CHECKLIST,
                        usuario=checklist.usuario,
                    )
                    expediente.estado = (
                        EstadoExpediente.PENDIENTE_REVALIDACION.value
                    )

                session.flush()
                resultado = a_schema(modelo)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise
