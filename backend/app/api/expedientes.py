from fastapi import APIRouter, File, HTTPException, UploadFile
from app.domain.estados import EstadoExpediente
from app.schemas.documento import DocumentoCreate, DocumentoRead
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead, ExpedienteUpdate
from app.schemas.historial import HistorialRead
from app.services.documentos import documento_service
from app.services.expedientes import expediente_service
from app.services.historial import historial_service

router = APIRouter()

@router.post("", response_model=ExpedienteRead)
def crear_expediente(data: ExpedienteCreate):
    expediente = expediente_service.crear(data)
    historial_service.registrar(expediente.id, "EXPEDIENTE_CREADO", detalle=f"Expediente {expediente.numero_interno}")
    return expediente

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
        expediente = expediente_service.actualizar(expediente_id, data)
        historial_service.registrar(expediente_id, "EXPEDIENTE_ACTUALIZADO")
        return expediente
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc

@router.post("/{expediente_id}/documentos", response_model=DocumentoRead)
def agregar_documento(expediente_id: str, data: DocumentoCreate):
    obtener_expediente(expediente_id)
    documento = documento_service.agregar(expediente_id, data)
    historial_service.registrar(expediente_id, "DOCUMENTO_AGREGADO", detalle=f"{documento.tipo}: {documento.nombre_archivo}")
    return documento

@router.get("/{expediente_id}/documentos", response_model=list[DocumentoRead])
def listar_documentos(expediente_id: str):
    obtener_expediente(expediente_id)
    return documento_service.listar_por_expediente(expediente_id)

@router.post("/{expediente_id}/documentos/op")
async def cargar_op(expediente_id: str, file: UploadFile = File(...)):
    try:
        expediente_service.cambiar_estado(expediente_id, EstadoExpediente.DOCUMENTACION_EN_CARGA)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc

    documento = documento_service.agregar(
        expediente_id,
        DocumentoCreate(
            tipo="OP",
            nombre_archivo=file.filename or "orden_pago.pdf",
            ruta=f"storage/expedientes/{expediente_id}/{file.filename}",
        ),
    )
    historial_service.registrar(expediente_id, "OP_CARGADA", detalle=documento.nombre_archivo)
    return {"expediente_id": expediente_id, "archivo": file.filename, "mensaje": "OP cargada. La extracción IA se integrará en el próximo sprint."}

@router.post("/{expediente_id}/validar", response_model=ExpedienteRead)
def validar_expediente(expediente_id: str):
    try:
        expediente = expediente_service.cambiar_estado(expediente_id, EstadoExpediente.VALIDADO)
        historial_service.registrar(expediente_id, "EXPEDIENTE_VALIDADO")
        return expediente
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc

@router.post("/{expediente_id}/generar-disposicion", response_model=ExpedienteRead)
def generar_disposicion(expediente_id: str):
    expediente = obtener_expediente(expediente_id)
    if expediente.estado != EstadoExpediente.VALIDADO:
        raise HTTPException(status_code=409, detail="El expediente debe estar VALIDADO antes de generar la disposición.")
    expediente = expediente_service.cambiar_estado(expediente_id, EstadoExpediente.DISPOSICION_EMITIDA)
    historial_service.registrar(expediente_id, "DISPOSICION_GENERADA")
    return expediente

@router.get("/{expediente_id}/historial", response_model=list[HistorialRead])
def listar_historial(expediente_id: str):
    obtener_expediente(expediente_id)
    return historial_service.listar_por_expediente(expediente_id)
