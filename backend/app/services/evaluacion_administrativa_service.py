from dataclasses import asdict
from uuid import uuid4

from app.domain.evaluacion_administrativa import EvaluacionAdministrativa
from app.schemas.evaluacion_administrativa import (
    EvaluacionAdministrativaCreate,
    EvaluacionAdministrativaRead,
)


class EvaluacionAdministrativaService:
    def __init__(self) -> None:
        self._evaluaciones: dict[str, EvaluacionAdministrativa] = {}

    def crear(
        self,
        data: EvaluacionAdministrativaCreate,
    ) -> EvaluacionAdministrativaRead:
        evaluacion_id = str(uuid4())
        evaluacion = EvaluacionAdministrativa(
            id_evaluacion=evaluacion_id,
            solicitud_intervencion_id=data.solicitud_intervencion_id,
            fecha_inicio=data.fecha_inicio,
            evaluador=data.evaluador,
            observaciones=data.observaciones,
        )
        self._evaluaciones[evaluacion_id] = evaluacion
        return EvaluacionAdministrativaRead(**asdict(evaluacion))

    def obtener_por_id(
        self,
        evaluacion_id: str,
    ) -> EvaluacionAdministrativaRead:
        evaluacion = self._evaluaciones[evaluacion_id]
        return EvaluacionAdministrativaRead(**asdict(evaluacion))

    def listar(self) -> list[EvaluacionAdministrativaRead]:
        return [
            EvaluacionAdministrativaRead(**asdict(evaluacion))
            for evaluacion in self._evaluaciones.values()
        ]


evaluacion_administrativa_service = EvaluacionAdministrativaService()
