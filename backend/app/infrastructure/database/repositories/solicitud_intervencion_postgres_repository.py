from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.solicitud_intervencion import (
    NumeroSolicitudDuplicadoError,
    SolicitudIntervencion,
)
from app.infrastructure.database.mappers.solicitud_intervencion_mapper import (
    a_dominio,
    a_modelo,
    actualizar_modelo,
)
from app.infrastructure.database.models.solicitud_intervencion_model import (
    SolicitudIntervencionModel,
)


class PostgresSolicitudIntervencionRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(self, solicitud: SolicitudIntervencion) -> None:
        with self._session_factory() as session:
            try:
                modelo = session.get(
                    SolicitudIntervencionModel,
                    solicitud.id_solicitud,
                )
                if modelo is None:
                    session.add(a_modelo(solicitud))
                else:
                    actualizar_modelo(modelo, solicitud)
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                diagnostico = getattr(exc.orig, "diag", None)
                constraint_name = getattr(
                    diagnostico,
                    "constraint_name",
                    None,
                )
                if constraint_name == (
                    "uq_solicitudes_intervencion_numero_solicitud"
                ):
                    raise NumeroSolicitudDuplicadoError(
                        "El número de solicitud ya existe."
                    ) from exc
                raise
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(
        self,
        solicitud_id: str,
    ) -> SolicitudIntervencion | None:
        with self._session_factory() as session:
            modelo = session.get(
                SolicitudIntervencionModel,
                solicitud_id,
            )
            if modelo is None:
                return None
            return a_dominio(modelo)

    def obtener_por_numero(
        self,
        numero_solicitud: str,
    ) -> SolicitudIntervencion | None:
        with self._session_factory() as session:
            consulta = select(SolicitudIntervencionModel).where(
                SolicitudIntervencionModel.numero_solicitud
                == numero_solicitud
            )
            modelo = session.scalar(consulta)
            if modelo is None:
                return None
            return a_dominio(modelo)

    def listar(self) -> list[SolicitudIntervencion]:
        with self._session_factory() as session:
            consulta = select(SolicitudIntervencionModel)
            modelos = session.scalars(consulta).all()
            return [a_dominio(modelo) for modelo in modelos]
