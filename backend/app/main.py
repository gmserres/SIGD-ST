from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.catalogos import router as catalogos_router
from app.api.expedientes import router as expedientes_router
from app.api.sistema import router as sistema_router
from app.core.settings import APP_STATE, APP_VERSION

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"

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
app.include_router(catalogos_router, prefix="/catalogos", tags=["Catálogos"])


@app.get("/")
def healthcheck():
    return {"sistema": "SIGD-ST", "estado": APP_STATE, "version": APP_VERSION}
