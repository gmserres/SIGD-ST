from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.infrastructure.database.mappers.validacion_administrativa_mapper import (
    a_modelo,
    a_schema,
)
from app.infrastructure.database.models.validacion_administrativa_model import (
    ValidacionAdministrativaModel,
)
from app.infrastructure.database.persistence.validacion_vigencia import (
    MOTIVO_REEMPLAZO_VALIDACION,
    invalidar_modelo,
    obtener_modelo_vigente,
)
from app.schemas.validacion import ValidacionAdministrativaRead


class PostgresValidacionAdministrativaRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def registrar(
        self,
        validacion: ValidacionAdministrativaRead,
    ) -> ValidacionAdministrativaRead:
        with self._session_factory() as session:
            try:
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
                modelo = a_modelo(validacion)
                session.add(modelo)
                session.flush()
                resultado = a_schema(modelo)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise

    def obtener_ultima_por_expediente(
        self,
        expediente_id: str,
    ) -> ValidacionAdministrativaRead | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ValidacionAdministrativaModel)
                .options(
                    selectinload(
                        ValidacionAdministrativaModel.controles
                    )
                )
                .where(
                    ValidacionAdministrativaModel.expediente_id
                    == expediente_id
                )
                .order_by(
                    ValidacionAdministrativaModel.fecha_validacion.desc(),
                    ValidacionAdministrativaModel.id.desc(),
                )
                .limit(1)
            )
            return a_schema(modelo) if modelo is not None else None

    def obtener_vigente(
        self,
        expediente_id: str,
    ) -> ValidacionAdministrativaRead | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ValidacionAdministrativaModel)
                .options(
                    selectinload(
                        ValidacionAdministrativaModel.controles
                    )
                )
                .where(
                    ValidacionAdministrativaModel.expediente_id
                    == expediente_id,
                    ValidacionAdministrativaModel.fecha_invalidacion.is_(
                        None
                    ),
                )
            )
            return a_schema(modelo) if modelo is not None else None

    def invalidar_vigente(
        self,
        expediente_id: str,
        motivo: str,
        usuario: str,
        fecha: datetime,
    ) -> ValidacionAdministrativaRead | None:
        with self._session_factory() as session:
            try:
                modelo = obtener_modelo_vigente(
                    session,
                    expediente_id,
                    bloquear=True,
                )
                if modelo is None:
                    return None
                invalidar_modelo(
                    modelo,
                    fecha=fecha,
                    motivo=motivo,
                    usuario=usuario,
                )
                session.flush()
                resultado = a_schema(modelo)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise

    def listar_por_expediente(
        self,
        expediente_id: str,
    ) -> list[ValidacionAdministrativaRead]:
        with self._session_factory() as session:
            modelos = session.scalars(
                select(ValidacionAdministrativaModel)
                .options(
                    selectinload(
                        ValidacionAdministrativaModel.controles
                    )
                )
                .where(
                    ValidacionAdministrativaModel.expediente_id
                    == expediente_id
                )
                .order_by(
                    ValidacionAdministrativaModel.fecha_validacion,
                    ValidacionAdministrativaModel.id,
                )
            ).all()
            return [a_schema(modelo) for modelo in modelos]
