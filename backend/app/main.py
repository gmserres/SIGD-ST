from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.catalogos import router as catalogos_router
from app.api.decisiones import router as decisiones_router
from app.api.expedientes import router as expedientes_router
from app.api.proveedores import router as proveedores_router
from app.api.selecciones_proveedor import router as selecciones_proveedor_router
from app.api.solicitudes import router as solicitudes_router
from app.api.sistema import router as sistema_router
from app.core.settings import APP_STATE, APP_VERSION, STORAGE_DIR

app = FastAPI(
    title="SIGD-ST API",
    version=APP_VERSION,
    description="API Alfa del Sistema Inteligente de Gestión Documental",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

app.include_router(sistema_router, prefix="/sistema", tags=["Sistema"])
app.include_router(expedientes_router, prefix="/expedientes", tags=["Expedientes"])
app.include_router(proveedores_router, prefix="/proveedores", tags=["Proveedores"])
app.include_router(decisiones_router, prefix="/decisiones", tags=["Decisiones"])
app.include_router(solicitudes_router, prefix="/solicitudes", tags=["Solicitudes"])
app.include_router(
    selecciones_proveedor_router,
    prefix="/solicitudes",
    tags=["Selección de Proveedor"],
)
app.include_router(catalogos_router, prefix="/catalogos", tags=["Catálogos"])


@app.get("/")
def healthcheck():
    return {"sistema": "SIGD-ST", "estado": APP_STATE, "version": APP_VERSION}
