from fastapi import APIRouter, HTTPException, status

from app.composition.proveedor import proveedor_service
from app.domain.proveedor import CuitProveedorDuplicadoError
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorEstadoUpdate,
    ProveedorRead,
    ProveedorUpdate,
)


router = APIRouter()


def _error_datos_invalidos(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "",
    response_model=ProveedorRead,
    status_code=status.HTTP_201_CREATED,
)
def registrar_proveedor(data: ProveedorCreate) -> ProveedorRead:
    try:
        return proveedor_service.registrar(data)
    except CuitProveedorDuplicadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except (TypeError, ValueError) as exc:
        raise _error_datos_invalidos(exc) from exc


@router.get("", response_model=list[ProveedorRead])
def listar_proveedores(
    buscar: str | None = None,
    activo: bool | None = None,
) -> list[ProveedorRead]:
    return proveedor_service.listar(
        buscar=buscar,
        activo=activo,
    )


@router.get("/{proveedor_id}", response_model=ProveedorRead)
def obtener_proveedor(proveedor_id: str) -> ProveedorRead:
    try:
        return proveedor_service.obtener_por_id(proveedor_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado.",
        ) from exc


@router.patch("/{proveedor_id}", response_model=ProveedorRead)
def modificar_proveedor(
    proveedor_id: str,
    data: ProveedorUpdate,
) -> ProveedorRead:
    try:
        return proveedor_service.modificar_razon_social(
            proveedor_id,
            data,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado.",
        ) from exc
    except (TypeError, ValueError) as exc:
        raise _error_datos_invalidos(exc) from exc


@router.patch(
    "/{proveedor_id}/estado",
    response_model=ProveedorRead,
)
def actualizar_estado_proveedor(
    proveedor_id: str,
    data: ProveedorEstadoUpdate,
) -> ProveedorRead:
    try:
        return proveedor_service.actualizar_estado(
            proveedor_id,
            data,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado.",
        ) from exc
