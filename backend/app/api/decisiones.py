from fastapi import APIRouter, HTTPException, status

from app.composition.solicitud_intervencion import solicitud_intervencion_service
from app.schemas.decision_expediente import CrearExpedienteDesdeDecision
from app.schemas.decision_administrativa import (
    DecisionAdministrativaCreate,
    DecisionAdministrativaRead,
)
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead
from app.services.decision_administrativa_service import (
    DecisionAprobatoriaDuplicadaError,
    decision_administrativa_service,
)
from app.composition.expediente import expediente_service


router = APIRouter()


@router.post(
    "",
    response_model=DecisionAdministrativaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_decision(
    data: DecisionAdministrativaCreate,
) -> DecisionAdministrativaRead:
    try:
        return decision_administrativa_service.crear(data)
    except DecisionAprobatoriaDuplicadaError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


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
            detail="La decisión no aprueba la intervención.",
        )

    if decision.fondo_interviniente is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La decisión no tiene un Fondo Interviniente determinado.",
        )

    if decision.fondo_interviniente != "FONDO_COMPENSADOR":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El circuito del Fondo Interviniente seleccionado todavía "
                "no está implementado."
            ),
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
