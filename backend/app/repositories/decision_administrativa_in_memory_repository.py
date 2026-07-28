from app.domain.decision_administrativa import DecisionAdministrativa
from app.repositories.decision_administrativa_repository import (
    DecisionAdministrativaYaRegistradaError,
)


class InMemoryDecisionAdministrativaRepository:
    def __init__(self) -> None:
        self._decisiones: dict[str, DecisionAdministrativa] = {}

    def guardar(self, decision: DecisionAdministrativa) -> None:
        if decision.id_decision in self._decisiones:
            raise DecisionAdministrativaYaRegistradaError(
                decision.id_decision
            )
        self._decisiones[decision.id_decision] = decision

    def obtener_por_id(
        self,
        decision_id: str,
    ) -> DecisionAdministrativa | None:
        return self._decisiones.get(decision_id)

    def listar(
        self,
        *,
        solicitud_intervencion_id: str | None = None,
    ) -> list[DecisionAdministrativa]:
        decisiones = sorted(
            self._decisiones.values(),
            key=lambda decision: (
                decision.fecha_decision,
                decision.id_decision,
            ),
        )

        if solicitud_intervencion_id is None:
            return decisiones

        return [
            decision
            for decision in decisiones
            if decision.solicitud_intervencion_id
            == solicitud_intervencion_id
        ]
