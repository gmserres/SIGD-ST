from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.finalizacion_expediente import (
    ESTADOS_TERMINALES_ORDINARIOS,
    ExpedienteTerminalError,
)
from app.infrastructure.database.models.expediente_model import ExpedienteModel


def bloquear_expediente_mutable(
    session: Session,
    expediente_id: str,
) -> ExpedienteModel | None:
    expediente = session.scalar(
        select(ExpedienteModel)
        .where(ExpedienteModel.id == expediente_id)
        .with_for_update()
    )
    if expediente is None:
        # Los repositorios conservan la traducción histórica de FK para una
        # referencia inexistente. La barrera sólo agrega semántica cuando el
        # Expediente real existe.
        return None
    if expediente.estado in ESTADOS_TERMINALES_ORDINARIOS:
        raise ExpedienteTerminalError(expediente_id, expediente.estado)
    return expediente
