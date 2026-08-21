from dataclasses import dataclass
from typing import Protocol

from app.infrastructure.database.models.decision_administrativa_model import (
    DecisionAdministrativaModel,
)
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.solicitud_intervencion_model import (
    SolicitudIntervencionModel,
)


@dataclass(frozen=True)
class FuentesTimelineSolicitud:
    solicitud: SolicitudIntervencionModel
    decisiones: list[DecisionAdministrativaModel]
    expedientes: list[ExpedienteModel]


class TimelineSolicitudRepository(Protocol):
    def obtener_fuentes(
        self,
        solicitud_id: str,
    ) -> FuentesTimelineSolicitud | None: ...
