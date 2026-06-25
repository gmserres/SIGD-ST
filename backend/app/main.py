from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.expedientes import router as expedientes_router

app = FastAPI(
    title="SIGD-ST API",
    version="0.1.0",
    description="API Alfa del Sistema Inteligente de Gestión Documental",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expedientes_router, prefix="/expedientes", tags=["Expedientes"])


@app.get("/")
def healthcheck():
    return {
        "sistema": "SIGD-ST",
        "estado": "ALFA",
        "version": "0.1.0",
    }
