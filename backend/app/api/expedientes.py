from fastapi import APIRouter, File, HTTPException, UploadFile

from app.domain.estados import EstadoExpediente
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead, ExpedienteUpdate
from app.services.expedientes import expediente_service

router = APIRouter()


@router.post("", response_model=ExpedienteRead)
def crear_expediente(data: ExpedienteCreate):
    return expediente_service.crear(data)


@router.get("", response_model=list[ExpedienteRead])
def listar_expedientes():
    return expediente_service.listar()


@router.get("/{expediente_id}", response_model=ExpedienteRead)
def obtener_expediente(expediente_id: str):
    try:
        return expediente_service.obtener(expediente_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc


@router.put("/{expediente_id}", response_model=ExpedienteRead)
def actualizar_expediente(expediente_id: str, data: ExpedienteUpdate):
    try:
        return expediente_service.actualizar(expediente_id, data)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc


@router.post("/{expediente_id}/documentos/op")
async def cargar_op(expediente_id: str, file: UploadFile = File(...)):
    try:
        expediente_service.cambiar_estado(expediente_id, EstadoExpediente.DOCUMENTACION_EN_CARGA)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc

    return {
        "expediente_id": expediente_id,
        "archivo": file.filename,
        "mensaje": "OP cargada. La extracción IA se integrará en el próximo sprint.",
    }


@router.post("/{expediente_id}/validar", response_model=ExpedienteRead)
def validar_expediente(expediente_id: str):
    try:
        return expediente_service.cambiar_estado(expediente_id, EstadoExpediente.VALIDADO)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc


@router.post("/{expediente_id}/generar-disposicion", response_model=ExpedienteRead)
def generar_disposicion(expediente_id: str):
    expediente = obtener_expediente(expediente_id)
    if expediente.estado != EstadoExpediente.VALIDADO:
        raise HTTPException(
            status_code=409,
            detail="El expediente debe estar VALIDADO antes de generar la disposición.",
        )
    return expediente_service.cambiar_estado(expediente_id, EstadoExpediente.DISPOSICION_EMITIDA)
