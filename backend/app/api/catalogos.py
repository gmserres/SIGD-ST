from fastapi import APIRouter
from app.schemas.establecimiento import EstablecimientoCreate, EstablecimientoRead
from app.schemas.proveedor import ProveedorCreate, ProveedorRead
from app.services.catalogos import catalogo_service

router = APIRouter()

# Catálogos temporales de demostración.
# Sus valores no representan definiciones funcionales definitivas.
EVALUADORES_TEMPORALES = [
    "Secretario Técnico",
    "Tesorero",
    "Secretaria Administrativa",
    "Presidente",
]

RESULTADOS_EVALUACION_TEMPORALES = [
    "Pendiente",
    "Favorable",
    "Desfavorable",
]

AUTORIDADES_DECISORAS_TEMPORALES = [
    "Secretario Técnico",
    "Tesorero",
    "Secretaria Administrativa",
    "Presidente",
]

RESULTADOS_DECISION_TEMPORALES = [
    "Aprobar intervención",
    "Rechazar intervención",
    "Pendiente de fondos",
]

FONDOS_INTERVINIENTES_TEMPORALES = [
    "FONDO_COMPENSADOR",
    "CUFP",
    "OTRO",
]

@router.post("/proveedores", response_model=ProveedorRead)
def crear_proveedor(data: ProveedorCreate):
    return catalogo_service.crear_proveedor(data)

@router.get("/proveedores", response_model=list[ProveedorRead])
def listar_proveedores():
    return catalogo_service.listar_proveedores()

@router.post("/establecimientos", response_model=EstablecimientoRead)
def crear_establecimiento(data: EstablecimientoCreate):
    return catalogo_service.crear_establecimiento(data)

@router.get("/establecimientos", response_model=list[EstablecimientoRead])
def listar_establecimientos():
    return catalogo_service.listar_establecimientos()

@router.get("/evaluadores", response_model=list[str])
def listar_evaluadores():
    return EVALUADORES_TEMPORALES

@router.get("/resultados-evaluacion", response_model=list[str])
def listar_resultados_evaluacion():
    return RESULTADOS_EVALUACION_TEMPORALES

@router.get("/autoridades-decisoras", response_model=list[str])
def listar_autoridades_decisoras():
    return AUTORIDADES_DECISORAS_TEMPORALES

@router.get("/resultados-decision", response_model=list[str])
def listar_resultados_decision():
    return RESULTADOS_DECISION_TEMPORALES

@router.get("/fondos-intervinientes", response_model=list[str])
def listar_fondos_intervinientes():
    return FONDOS_INTERVINIENTES_TEMPORALES
