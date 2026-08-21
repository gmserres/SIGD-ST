from fastapi import APIRouter, HTTPException, status

from app.composition.seleccion_proveedor import seleccion_proveedor_service
from app.domain.seleccion_proveedor import (
    DecisionNoAprobatoriaError,
    DecisionSeleccionInexistenteError,
    DecisionSolicitudInconsistenteError,
    ExpedienteSeleccionIncompletoError,
    ExpedienteSeleccionInexistenteError,
    FondoSeleccionIncompatibleError,
    MismoProveedorSeleccionadoError,
    ProveedorInactivoError,
    ProveedorSeleccionInexistenteError,
    SeleccionProveedorInexistenteError,
    SeleccionProveedorVigenteError,
    SolicitudSeleccionInexistenteError,
)
from app.schemas.seleccion_proveedor import ReemplazoProveedorCreate, SeleccionProveedorCreate, SeleccionProveedorRead
from app.domain.finalizacion_expediente import ExpedienteTerminalError


router = APIRouter()
ERRORES_NO_ENCONTRADOS = (
    ExpedienteSeleccionInexistenteError,
    SolicitudSeleccionInexistenteError,
    DecisionSeleccionInexistenteError,
    ProveedorSeleccionInexistenteError,
    SeleccionProveedorInexistenteError,
)
ERRORES_CONFLICTO = (
    ExpedienteSeleccionIncompletoError,
    FondoSeleccionIncompatibleError,
    DecisionNoAprobatoriaError,
    DecisionSolicitudInconsistenteError,
    ProveedorInactivoError,
    SeleccionProveedorVigenteError,
    MismoProveedorSeleccionadoError,
    ExpedienteTerminalError,
)


def _traducir_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ERRORES_NO_ENCONTRADOS):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ERRORES_CONFLICTO):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post("/{expediente_id}/seleccion-proveedor", response_model=SeleccionProveedorRead, status_code=status.HTTP_201_CREATED)
def seleccionar_proveedor(expediente_id: str, data: SeleccionProveedorCreate) -> SeleccionProveedorRead:
    try:
        return seleccion_proveedor_service.seleccionar(expediente_id, data)
    except (
        ExpedienteSeleccionInexistenteError,
        ExpedienteSeleccionIncompletoError,
        FondoSeleccionIncompatibleError,
        SolicitudSeleccionInexistenteError,
        DecisionSeleccionInexistenteError,
        ProveedorSeleccionInexistenteError,
        DecisionNoAprobatoriaError,
        DecisionSolicitudInconsistenteError,
        ProveedorInactivoError,
        SeleccionProveedorVigenteError,
        TypeError,
        ValueError,
        ExpedienteTerminalError,
    ) as exc:
        raise _traducir_error(exc) from exc


@router.get("/{expediente_id}/seleccion-proveedor", response_model=SeleccionProveedorRead)
def obtener_seleccion_vigente(expediente_id: str) -> SeleccionProveedorRead:
    try:
        return seleccion_proveedor_service.obtener_vigente(expediente_id)
    except (
        ExpedienteSeleccionInexistenteError,
        ExpedienteSeleccionIncompletoError,
        SolicitudSeleccionInexistenteError,
        SeleccionProveedorInexistenteError,
        DecisionSeleccionInexistenteError,
        DecisionNoAprobatoriaError,
        FondoSeleccionIncompatibleError,
        DecisionSolicitudInconsistenteError,
    ) as exc:
        raise _traducir_error(exc) from exc


@router.post("/{expediente_id}/seleccion-proveedor/reemplazos", response_model=SeleccionProveedorRead, status_code=status.HTTP_201_CREATED)
def reemplazar_proveedor(expediente_id: str, data: ReemplazoProveedorCreate) -> SeleccionProveedorRead:
    try:
        return seleccion_proveedor_service.reemplazar(expediente_id, data)
    except (
        ExpedienteSeleccionInexistenteError,
        ExpedienteSeleccionIncompletoError,
        FondoSeleccionIncompatibleError,
        SolicitudSeleccionInexistenteError,
        DecisionSeleccionInexistenteError,
        ProveedorSeleccionInexistenteError,
        SeleccionProveedorInexistenteError,
        DecisionNoAprobatoriaError,
        DecisionSolicitudInconsistenteError,
        ProveedorInactivoError,
        SeleccionProveedorVigenteError,
        MismoProveedorSeleccionadoError,
        TypeError,
        ValueError,
        ExpedienteTerminalError,
    ) as exc:
        raise _traducir_error(exc) from exc


@router.get("/{expediente_id}/seleccion-proveedor/historial", response_model=list[SeleccionProveedorRead])
def listar_selecciones_proveedor(expediente_id: str) -> list[SeleccionProveedorRead]:
    try:
        return seleccion_proveedor_service.listar_historial(expediente_id)
    except (
        ExpedienteSeleccionInexistenteError,
        ExpedienteSeleccionIncompletoError,
        SolicitudSeleccionInexistenteError,
    ) as exc:
        raise _traducir_error(exc) from exc
