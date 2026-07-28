from dataclasses import asdict
from uuid import uuid4

from app.domain.decision_administrativa import DecisionAdministrativa
from app.repositories.decision_administrativa_in_memory_repository import (
    InMemoryDecisionAdministrativaRepository,
)
from app.repositories.decision_administrativa_repository import (
    DecisionAdministrativaRepository,
)
from app.schemas.decision_administrativa import (
    DecisionAdministrativaCreate,
    DecisionAdministrativaRead,
)


class DecisionAprobatoriaDuplicadaError(ValueError):
    pass


class DecisionAdministrativaService:
    def __init__(
        self,
        repository: DecisionAdministrativaRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            if repository is not None
            else InMemoryDecisionAdministrativaRepository()
        )

    def crear(
        self,
        data: DecisionAdministrativaCreate,
    ) -> DecisionAdministrativaRead:
        if (
            data.resultado == "Aprobar intervención"
            and any(
                decision.resultado == "Aprobar intervención"
                for decision in self._repository.listar(
                    solicitud_intervencion_id=data.solicitud_intervencion_id
                )
            )
        ):
            raise DecisionAprobatoriaDuplicadaError(
                "La intervención ya fue aprobada."
            )

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
        self._repository.guardar(decision)
        return DecisionAdministrativaRead(**asdict(decision))

    def obtener_por_id(
        self,
        decision_id: str,
    ) -> DecisionAdministrativaRead:
        decision = self._repository.obtener_por_id(decision_id)
        if decision is None:
            raise KeyError(decision_id)
        return DecisionAdministrativaRead(**asdict(decision))

    def listar(self) -> list[DecisionAdministrativaRead]:
        return [
            DecisionAdministrativaRead(**asdict(decision))
            for decision in self._repository.listar()
        ]
