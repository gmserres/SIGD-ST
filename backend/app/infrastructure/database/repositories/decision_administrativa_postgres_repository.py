from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.decision_administrativa import DecisionAdministrativa
from app.infrastructure.database.mappers.decision_administrativa_mapper import (
    a_dominio,
    a_modelo,
)
from app.infrastructure.database.models.decision_administrativa_model import (
    DecisionAdministrativaModel,
)
from app.repositories.decision_administrativa_repository import (
    DecisionAdministrativaYaRegistradaError,
)


class PostgresDecisionAdministrativaRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(self, decision: DecisionAdministrativa) -> None:
        with self._session_factory() as session:
            try:
                modelo = session.get(
                    DecisionAdministrativaModel,
                    decision.id_decision,
                )
                if modelo is not None:
                    raise DecisionAdministrativaYaRegistradaError(
                        decision.id_decision
                    )

                session.add(a_modelo(decision))
                session.commit()
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(
        self,
        decision_id: str,
    ) -> DecisionAdministrativa | None:
        with self._session_factory() as session:
            modelo = session.get(
                DecisionAdministrativaModel,
                decision_id,
            )
            if modelo is None:
                return None
            return a_dominio(modelo)

    def listar(
        self,
        *,
        solicitud_intervencion_id: str | None = None,
    ) -> list[DecisionAdministrativa]:
        with self._session_factory() as session:
            consulta = select(DecisionAdministrativaModel)

            if solicitud_intervencion_id is not None:
                consulta = consulta.where(
                    DecisionAdministrativaModel.solicitud_intervencion_id
                    == solicitud_intervencion_id
                )

            consulta = consulta.order_by(
                DecisionAdministrativaModel.fecha_decision,
                DecisionAdministrativaModel.id_decision,
            )
            modelos = session.scalars(consulta).all()
            return [a_dominio(modelo) for modelo in modelos]
