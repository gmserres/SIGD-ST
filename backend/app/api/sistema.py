from app.core.settings import APP_NAME, APP_STATE, APP_VERSION
from fastapi import APIRouter

router = APIRouter()


@router.get("/estado")
def estado_sistema():
    return {
        "sistema": APP_NAME,
        "estado": APP_STATE,
        "version": APP_VERSION,
        "modulos": [
            "expedientes",
            "documentos",
            "historial",
            "catalogos",
            "analisis_op_alfa",
            "validaciones",
        ],
    }
