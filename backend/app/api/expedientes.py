from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.storage import guardar_upload
from app.domain.estados import EstadoExpediente
from app.schemas.analisis_op import AnalisisOPRead
from app.schemas.documento import DocumentoCreate, DocumentoRead
from app.schemas.disposicion import DisposicionRead, DisposicionUpdate
from app.schemas.checklist_fisico import ChecklistFisicoCreate, ChecklistFisicoRead
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead, ExpedienteUpdate
from app.schemas.historial import HistorialRead
from app.schemas.texto_documento import TextoDocumentoRead
from app.schemas.validacion import ValidacionExpedienteRead
from app.schemas.validacion_observada import ValidacionObservadaCreate
from app.services.analisis_op import analisis_op_service
from app.services.documentos import documento_service
from app.services.disposiciones import disposicion_service
from app.services.checklist_fisico import checklist_fisico_service
from app.services.expedientes import expediente_service
from app.services.historial import historial_service
from app.services.texto_documento import texto_documento_service
from app.services.validaciones import validacion_service

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


@router.post("/{expediente_id}/documentos/upload", response_model=DocumentoRead)
async def subir_documento(
    expediente_id: str,
    tipo: str = Form(...),
    observaciones: str | None = Form(default=None),
    file: UploadFile = File(...),
):
    obtener_expediente(expediente_id)
    nombre_original, ruta_relativa, tamano_bytes, mime_type = await guardar_upload(expediente_id, file, tipo.lower())
    documento = documento_service.agregar(
        expediente_id,
        DocumentoCreate(
            tipo=tipo,
            nombre_archivo=nombre_original,
            ruta=ruta_relativa,
            observaciones=observaciones,
            tamano_bytes=tamano_bytes,
            mime_type=mime_type,
        ),
    )
    historial_service.registrar(expediente_id, "DOCUMENTO_CARGADO", detalle=f"{tipo}: {nombre_original}")
    return documento


@router.get("/{expediente_id}/documentos", response_model=list[DocumentoRead])
def listar_documentos(expediente_id: str):
    obtener_expediente(expediente_id)
    return documento_service.listar_por_expediente(expediente_id)


def _obtener_documento_o_404(expediente_id: str, documento_id: str) -> DocumentoRead:
    obtener_expediente(expediente_id)
    documento = documento_service.obtener(expediente_id, documento_id)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return documento


@router.get("/{expediente_id}/documentos/{documento_id}/descargar")
def descargar_documento(expediente_id: str, documento_id: str):
    documento = _obtener_documento_o_404(expediente_id, documento_id)
    ruta = Path(__file__).resolve().parents[3] / documento.ruta
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado")
    return FileResponse(path=ruta, filename=documento.nombre_archivo)


@router.get("/{expediente_id}/documentos/{documento_id}/vista-previa")
def vista_previa_documento(expediente_id: str, documento_id: str):
    documento = _obtener_documento_o_404(expediente_id, documento_id)
    ruta = Path(__file__).resolve().parents[3] / documento.ruta
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado")
    return FileResponse(path=ruta, media_type=documento.mime_type or "application/octet-stream")


@router.get("/{expediente_id}/documentos/{documento_id}/texto", response_model=TextoDocumentoRead)
def extraer_texto_documento(expediente_id: str, documento_id: str):
    _obtener_documento_o_404(expediente_id, documento_id)
    texto = texto_documento_service.extraer(expediente_id, documento_id)
    historial_service.registrar(expediente_id, "TEXTO_DOCUMENTO_EXTRAIDO", detalle=documento_id)
    return texto


@router.post("/{expediente_id}/documentos/op", response_model=DocumentoRead)
async def cargar_op(expediente_id: str, file: UploadFile = File(...)):
    try:
        expediente_service.cambiar_estado(expediente_id, EstadoExpediente.DOCUMENTACION_EN_CARGA)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Expediente no encontrado") from exc

    nombre_original, ruta_relativa, tamano_bytes, mime_type = await guardar_upload(expediente_id, file, "op")
    documento = documento_service.agregar(
        expediente_id,
        DocumentoCreate(
            tipo="OP",
            nombre_archivo=nombre_original,
            ruta=ruta_relativa,
            observaciones="Orden de Pago cargada desde la ficha del expediente.",
            tamano_bytes=tamano_bytes,
            mime_type=mime_type,
        ),
    )
    historial_service.registrar(expediente_id, "OP_CARGADA", detalle=documento.nombre_archivo)
    return documento


@router.post("/{expediente_id}/analizar-op", response_model=AnalisisOPRead)
def analizar_op(expediente_id: str):
    obtener_expediente(expediente_id)
    if not validacion_service.tiene_op(expediente_id):
        historial_service.registrar(expediente_id, "ANALISIS_OP_BLOQUEADO", detalle="No existe OP cargada.")
    analisis = analisis_op_service.analizar(expediente_id)
    historial_service.registrar(expediente_id, "OP_ANALIZADA_IA", detalle=f"Modo {analisis.modo}")
    return analisis


@router.get("/{expediente_id}/checklist-fisico", response_model=ChecklistFisicoRead | None)
def obtener_checklist_fisico(expediente_id: str):
    obtener_expediente(expediente_id)
    return checklist_fisico_service.obtener(expediente_id)


@router.post("/{expediente_id}/checklist-fisico", response_model=ChecklistFisicoRead)
def guardar_checklist_fisico(expediente_id: str, data: ChecklistFisicoCreate):
    obtener_expediente(expediente_id)
    checklist = checklist_fisico_service.guardar(expediente_id, data)
    return checklist


@router.get("/{expediente_id}/validacion", response_model=ValidacionExpedienteRead)
def validar_controles_expediente(expediente_id: str):
    obtener_expediente(expediente_id)
    return validacion_service.validar(expediente_id)


@router.post("/{expediente_id}/validar", response_model=ExpedienteRead)
def validar_expediente(expediente_id: str):
    obtener_expediente(expediente_id)
    resultado = validacion_service.validar(expediente_id, registrar_historial=False)

    if resultado.errores:
        historial_service.registrar(expediente_id, "VALIDACION_BLOQUEADA", detalle=" | ".join(resultado.errores))
        raise HTTPException(
            status_code=409,
            detail={"mensaje": "No se puede validar el expediente. Existen errores críticos.", "errores": resultado.errores},
        )

    if resultado.advertencias:
        historial_service.registrar(expediente_id, "VALIDACION_REQUIERE_OBSERVACIONES", detalle=" | ".join(resultado.advertencias))
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "El expediente tiene observaciones. Para continuar use Validar con observaciones.",
                "advertencias": resultado.advertencias,
            },
        )

    expediente = expediente_service.cambiar_estado(expediente_id, EstadoExpediente.VALIDADO)
    historial_service.registrar(expediente_id, "EXPEDIENTE_VALIDADO")
    return expediente


@router.post("/{expediente_id}/validar-con-observaciones", response_model=ExpedienteRead)
def validar_expediente_con_observaciones(expediente_id: str, data: ValidacionObservadaCreate):
    obtener_expediente(expediente_id)
    resultado = validacion_service.validar(expediente_id, registrar_historial=False)

    if resultado.errores:
        historial_service.registrar(expediente_id, "VALIDACION_OBSERVADA_BLOQUEADA", detalle=" | ".join(resultado.errores))
        raise HTTPException(
            status_code=409,
            detail={"mensaje": "No se puede validar ni siquiera con observaciones. Existen errores críticos.", "errores": resultado.errores},
        )

    if len(data.motivo.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail={"mensaje": "Debe ingresar un motivo administrativo suficiente para validar con observaciones."},
        )

    detalle = f"Motivo: {data.motivo.strip()}"
    if resultado.advertencias:
        detalle += " | Observaciones: " + " | ".join(resultado.advertencias)

    expediente = expediente_service.cambiar_estado(expediente_id, EstadoExpediente.VALIDADO)
    historial_service.registrar(
        expediente_id,
        "EXPEDIENTE_VALIDADO_CON_OBSERVACIONES",
        usuario=data.usuario,
        detalle=detalle,
    )
    return expediente


@router.post("/{expediente_id}/disposicion/borrador", response_model=DisposicionRead)
def generar_borrador_disposicion(expediente_id: str, regenerar: bool = False):
    expediente = obtener_expediente(expediente_id)
    if expediente.estado != EstadoExpediente.VALIDADO:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "Para generar el borrador de disposición, el expediente debe estar validado o validado con observaciones.",
                "errores": ["El expediente debe estar VALIDADO."],
            },
        )
    return disposicion_service.generar_borrador(expediente_id, regenerar=regenerar)


@router.get("/{expediente_id}/disposicion/borrador", response_model=DisposicionRead)
def obtener_borrador_disposicion(expediente_id: str):
    obtener_expediente(expediente_id)
    return disposicion_service.obtener(expediente_id)


@router.put("/{expediente_id}/disposicion/borrador", response_model=DisposicionRead)
def actualizar_borrador_disposicion(expediente_id: str, data: DisposicionUpdate):
    obtener_expediente(expediente_id)
    return disposicion_service.actualizar_borrador(expediente_id, data)



@router.post("/{expediente_id}/generar-disposicion", response_model=ExpedienteRead)
def generar_disposicion(expediente_id: str):
    expediente = obtener_expediente(expediente_id)
    errores = validacion_service.errores_bloqueantes(expediente_id)
    if errores:
        historial_service.registrar(expediente_id, "GENERACION_DISPOSICION_BLOQUEADA", detalle=" | ".join(errores))
        raise HTTPException(
            status_code=409,
            detail={"mensaje": "No se puede generar la disposición. Existen errores críticos.", "errores": errores},
        )
    if expediente.estado != EstadoExpediente.VALIDADO:
        historial_service.registrar(expediente_id, "GENERACION_DISPOSICION_BLOQUEADA", detalle="El expediente no está validado.")
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "No se puede generar la disposición. El expediente debe estar validado.",
                "errores": ["El expediente debe estar VALIDADO antes de generar la disposición."],
            },
        )

    expediente = expediente_service.cambiar_estado(expediente_id, EstadoExpediente.DISPOSICION_EMITIDA)
    historial_service.registrar(expediente_id, "DISPOSICION_GENERADA")
    return expediente


@router.get("/{expediente_id}/historial", response_model=list[HistorialRead])
def listar_historial(expediente_id: str):
    obtener_expediente(expediente_id)
    return historial_service.listar_por_expediente(expediente_id)
