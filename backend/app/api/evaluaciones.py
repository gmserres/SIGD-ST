from fastapi import APIRouter, HTTPException, status

from app.schemas.evaluacion_administrativa import (
    EvaluacionAdministrativaCreate,
    EvaluacionAdministrativaRead,
)
from app.services.evaluacion_administrativa_service import (
    evaluacion_administrativa_service,
)


router = APIRouter()


@router.post(
    "",
    response_model=EvaluacionAdministrativaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_evaluacion(
    data: EvaluacionAdministrativaCreate,
) -> EvaluacionAdministrativaRead:
    return evaluacion_administrativa_service.crear(data)


@router.get("", response_model=list[EvaluacionAdministrativaRead])
def listar_evaluaciones() -> list[EvaluacionAdministrativaRead]:
    return evaluacion_administrativa_service.listar()


@router.get("/{evaluacion_id}", response_model=EvaluacionAdministrativaRead)
def obtener_evaluacion(evaluacion_id: str) -> EvaluacionAdministrativaRead:
    try:
        return evaluacion_administrativa_service.obtener_por_id(evaluacion_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluación Administrativa no encontrada",
        ) from exc
