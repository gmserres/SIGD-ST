from fastapi import APIRouter, HTTPException, status

from app.composition.solicitud_intervencion import (
    solicitud_intervencion_service,
)
from app.domain.solicitud_intervencion import (
    NumeroSolicitudDuplicadoError,
)
from app.schemas.solicitud_intervencion import (
    SolicitudIntervencionCreate,
    SolicitudIntervencionRead,
    SolicitudIntervencionUpdate,
)


router = APIRouter()


@router.post(
    "",
    response_model=SolicitudIntervencionRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_solicitud(
    data: SolicitudIntervencionCreate,
) -> SolicitudIntervencionRead:
    try:
        return solicitud_intervencion_service.crear(data)
    except NumeroSolicitudDuplicadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.put(
    "/{solicitud_id}",
    response_model=SolicitudIntervencionRead,
    status_code=status.HTTP_200_OK,
)
def actualizar_solicitud(
    solicitud_id: str,
    data: SolicitudIntervencionUpdate,
) -> SolicitudIntervencionRead:
    try:
        return solicitud_intervencion_service.actualizar(
            solicitud_id,
            data,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de Intervención no encontrada",
        ) from exc
    except NumeroSolicitudDuplicadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[SolicitudIntervencionRead])
def listar_solicitudes() -> list[SolicitudIntervencionRead]:
    return solicitud_intervencion_service.listar()


@router.get("/{solicitud_id}", response_model=SolicitudIntervencionRead)
def obtener_solicitud(solicitud_id: str) -> SolicitudIntervencionRead:
    try:
        return solicitud_intervencion_service.obtener_por_id(solicitud_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud de Intervención no encontrada",
        ) from exc
