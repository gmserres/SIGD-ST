from typing import Protocol

from app.domain.decision_administrativa import DecisionAdministrativa


class DecisionAdministrativaYaRegistradaError(ValueError):
    def __init__(self, decision_id: str) -> None:
        self.decision_id = decision_id
        super().__init__(
            f"La Decisión Administrativa {decision_id} ya está registrada."
        )


class DecisionAdministrativaRepository(Protocol):
    def guardar(self, decision: DecisionAdministrativa) -> None:
        ...

    def obtener_por_id(
        self,
        decision_id: str,
    ) -> DecisionAdministrativa | None:
        ...

    def listar(
        self,
        *,
        solicitud_intervencion_id: str | None = None,
    ) -> list[DecisionAdministrativa]:
        ...
