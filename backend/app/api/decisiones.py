from fastapi import APIRouter, HTTPException, status

from app.schemas.decision_administrativa import (
    DecisionAdministrativaCreate,
    DecisionAdministrativaRead,
)
from app.services.decision_administrativa_service import (
    decision_administrativa_service,
)


router = APIRouter()


@router.post(
    "",
    response_model=DecisionAdministrativaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_decision(
    data: DecisionAdministrativaCreate,
) -> DecisionAdministrativaRead:
    return decision_administrativa_service.crear(data)


@router.get("", response_model=list[DecisionAdministrativaRead])
def listar_decisiones() -> list[DecisionAdministrativaRead]:
    return decision_administrativa_service.listar()


@router.get("/{decision_id}", response_model=DecisionAdministrativaRead)
def obtener_decision(decision_id: str) -> DecisionAdministrativaRead:
    try:
        return decision_administrativa_service.obtener_por_id(decision_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decisión Administrativa no encontrada",
        ) from exc
