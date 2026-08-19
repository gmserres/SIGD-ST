from fastapi import APIRouter, HTTPException

from app.composition.formalizacion_disposicion import (
    formalizacion_disposicion_service,
)
from app.repositories.formalizacion_disposicion_persistence import (
    DisposicionNoEncontradaAlFormalizarError,
    DisposicionYaFormalizadaError,
    ExpedienteDisposicionNoEncontradoError,
    FechaFormalizacionAnteriorAEmisionError,
)
from app.schemas.disposicion import DisposicionEmitidaRead
from app.schemas.formalizacion_disposicion import (
    FormalizacionDisposicionCreate,
)
from app.services.formalizacion_disposicion import (
    FechaFormalizacionFuturaError,
)
from app.domain.finalizacion_expediente import ExpedienteTerminalError


router = APIRouter()


@router.post(
    "/{id_disposicion}/formalizacion",
    response_model=DisposicionEmitidaRead,
)
def formalizar_disposicion(
    id_disposicion: str,
    data: FormalizacionDisposicionCreate,
):
    try:
        return formalizacion_disposicion_service.formalizar(
            id_disposicion,
            data.fecha_formalizacion,
        )
    except (
        DisposicionNoEncontradaAlFormalizarError,
        ExpedienteDisposicionNoEncontradoError,
    ) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (DisposicionYaFormalizadaError, ExpedienteTerminalError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (
        FechaFormalizacionFuturaError,
        FechaFormalizacionAnteriorAEmisionError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
