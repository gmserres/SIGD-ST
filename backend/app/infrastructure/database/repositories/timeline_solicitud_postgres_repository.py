from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.models.decision_administrativa_model import (
    DecisionAdministrativaModel,
)
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.solicitud_intervencion_model import (
    SolicitudIntervencionModel,
)
from app.repositories.timeline_solicitud_repository import (
    FuentesTimelineSolicitud,
)


class PostgresTimelineSolicitudRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def obtener_fuentes(
        self,
        solicitud_id: str,
    ) -> FuentesTimelineSolicitud | None:
        with self._session_factory() as session:
            solicitud = session.get(
                SolicitudIntervencionModel,
                solicitud_id,
            )
            if solicitud is None:
                return None
            decisiones = list(
                session.scalars(
                    select(DecisionAdministrativaModel)
                    .where(
                        DecisionAdministrativaModel.solicitud_intervencion_id
                        == solicitud_id
                    )
                    .order_by(
                        DecisionAdministrativaModel.fecha_decision,
                        DecisionAdministrativaModel.id_decision,
                    )
                ).all()
            )
            expedientes = list(
                session.scalars(
                    select(ExpedienteModel)
                    .where(
                        ExpedienteModel.solicitud_intervencion_id
                        == solicitud_id
                    )
                    .order_by(
                        ExpedienteModel.creado,
                        ExpedienteModel.secuencia,
                    )
                ).all()
            )
            session.expunge_all()
            return FuentesTimelineSolicitud(
                solicitud=solicitud,
                decisiones=decisiones,
                expedientes=expedientes,
            )
