from fastapi import APIRouter, HTTPException, status

from app.schemas.decision_expediente import CrearExpedienteDesdeDecision
from app.schemas.decision_administrativa import (
    DecisionAdministrativaCreate,
    DecisionAdministrativaRead,
)
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead
from app.services.decision_administrativa_service import (
    decision_administrativa_service,
)
from app.services.expedientes import expediente_service
from app.services.solicitud_intervencion_service import solicitud_intervencion_service


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


@router.post(
    "/{decision_id}/expedientes",
    response_model=ExpedienteRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_expediente_desde_decision(
    decision_id: str,
    data: CrearExpedienteDesdeDecision,
) -> ExpedienteRead:
    try:
        decision = decision_administrativa_service.obtener_por_id(decision_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decisión Administrativa no encontrada",
        ) from exc

    if decision.resultado != "Aprobar intervención":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La decisión no habilita la creación de un expediente.",
        )

    try:
        solicitud = solicitud_intervencion_service.obtener_por_id(
            decision.solicitud_intervencion_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de Intervención no encontrada",
        ) from exc

    expediente = ExpedienteCreate(
        numero_interno=data.numero_interno,
        numero_gdeba=data.numero_gdeba,
        tipo_tramite=data.tipo_tramite,
        solicitud_intervencion_id=solicitud.id_solicitud,
        decision_administrativa_id=decision.id_decision,
        id_suna=solicitud.id_suna,
        establecimiento=solicitud.establecimiento,
        objeto=solicitud.motivo,
    )
    return expediente_service.crear(expediente)


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
