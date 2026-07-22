from dataclasses import asdict
from uuid import uuid4

from app.domain.decision_administrativa import DecisionAdministrativa
from app.schemas.decision_administrativa import (
    DecisionAdministrativaCreate,
    DecisionAdministrativaRead,
)


class DecisionAdministrativaService:
    def __init__(self) -> None:
        self._decisiones: dict[str, DecisionAdministrativa] = {}

    def crear(
        self,
        data: DecisionAdministrativaCreate,
    ) -> DecisionAdministrativaRead:
        decision_id = str(uuid4())
        decision = DecisionAdministrativa(
            id_decision=decision_id,
            solicitud_intervencion_id=data.solicitud_intervencion_id,
            autoridad_decisora=data.autoridad_decisora,
            fecha_decision=data.fecha_decision,
            resultado=data.resultado,
            fundamento=data.fundamento,
            fondo_interviniente=data.fondo_interviniente,
            descripcion_fondo=data.descripcion_fondo,
            usuario_registrante=data.usuario_registrante,
        )
        self._decisiones[decision_id] = decision
        return DecisionAdministrativaRead(**asdict(decision))

    def obtener_por_id(
        self,
        decision_id: str,
    ) -> DecisionAdministrativaRead:
        decision = self._decisiones[decision_id]
        return DecisionAdministrativaRead(**asdict(decision))

    def listar(self) -> list[DecisionAdministrativaRead]:
        return [
            DecisionAdministrativaRead(**asdict(decision))
            for decision in self._decisiones.values()
        ]


decision_administrativa_service = DecisionAdministrativaService()
