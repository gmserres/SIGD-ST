from fastapi import APIRouter
from app.schemas.establecimiento import EstablecimientoCreate, EstablecimientoRead
from app.schemas.proveedor import ProveedorCreate, ProveedorRead
from app.services.catalogos import catalogo_service

router = APIRouter()

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
