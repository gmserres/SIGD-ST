from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models.validacion_administrativa_model import (
    ValidacionAdministrativaModel,
)


MOTIVO_REEMPLAZO_VALIDACION = (
    "Reemplazada por nueva validación administrativa"
)
MOTIVO_CAMBIO_CHECKLIST = (
    "Modificación del checklist físico posterior a la validación"
)
MOTIVO_CARGA_OP = "Carga de OP posterior a la validación administrativa"
USUARIO_CAMBIO_MATERIAL = "Secretario Técnico"


def obtener_modelo_vigente(
    session: Session,
    expediente_id: str,
    *,
    bloquear: bool = False,
) -> ValidacionAdministrativaModel | None:
    consulta = select(ValidacionAdministrativaModel).where(
        ValidacionAdministrativaModel.expediente_id == expediente_id,
        ValidacionAdministrativaModel.fecha_invalidacion.is_(None),
    )
    if bloquear:
        consulta = consulta.with_for_update()
    return session.scalar(consulta)


def invalidar_modelo(
    modelo: ValidacionAdministrativaModel,
    *,
    fecha: datetime,
    motivo: str,
    usuario: str,
) -> None:
    if modelo.fecha_invalidacion is not None:
        return
    modelo.fecha_invalidacion = fecha
    modelo.motivo_invalidacion = motivo
    modelo.usuario_invalidacion = usuario
