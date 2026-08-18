from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, PlainTextResponse
from pathlib import Path

from app.core.storage import guardar_upload
from app.domain.estados import EstadoExpediente
from app.schemas.analisis_op import AnalisisOPRead
from app.schemas.control_proveedor_op import ControlProveedorOPRead
from app.schemas.control_proveedor_op_registro import (
    ControlProveedorOPRegistroRead,
)
from app.schemas.documento import DocumentoCreate, DocumentoRead
from app.schemas.disposicion import (
    DisposicionEmitirCreate,
    DisposicionEmitidaRead,
    DisposicionRead,
    DisposicionUpdate,
)
from app.schemas.checklist_fisico import ChecklistFisicoCreate, ChecklistFisicoRead
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead, ExpedienteUpdate
from app.schemas.firma import RegistroFirmaCreate
from app.schemas.archivo import RegistroArchivoCreate
from app.schemas.historial import HistorialRead
from app.schemas.habilitacion_proveedor_op import (
    HabilitacionProveedorOPRead,
)
from app.schemas.parametros import ParametrosInstitucionalesRead, ParametrosInstitucionalesUpdate
from app.schemas.texto_documento import TextoDocumentoRead
from app.schemas.validacion import ValidacionExpedienteRead
from app.schemas.validacion_observada import ValidacionObservadaCreate
from app.composition.analisis_op import analisis_op_service
from app.composition.control_proveedor_op import (
    control_proveedor_op_service,
    registrar_control_proveedor_op_service,
)
from app.composition.habilitacion_proveedor_op import (
    evaluar_habilitacion_proveedor_op_service,
)
from app.composition.disposicion import (
    consulta_disposicion_service,
    disposicion_docx_service,
    emision_disposicion_service,
    registro_firma_service,
    registro_archivo_service,
)
from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ConfiguracionUCVigenteNoEncontradaError,
)
from app.services.analisis_op import (
    ArchivoOPNoAnalizableError,
    ArchivoOPNoDisponibleError,
    ConfiguracionUCNoAsociadaError,
    ConfiguracionUCHistoricaNoEncontradaError,
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)
from app.composition.documento import documento_service
from app.services.disposiciones import (
    BorradorDisposicionNoHabilitadoError,
    BorradorDisposicionObsoletoError,
    DisposicionOPAmbiguaError,
    DisposicionOPNoEncontradaError,
    disposicion_service,
)
from app.repositories.disposicion_repository import (
    DisposicionYaRegistradaError,
)
from app.repositories.control_proveedor_op_repository import (
    SeleccionControlObsoletaError,
)
from app.repositories.emitir_disposicion_persistence import (
    ContextoEmisionObsoletoError,
    EstadoExpedienteIncompatibleError,
    ExpedienteNoEncontradoAlEmitirError,
)
from app.services.consulta_disposicion import (
    DisposicionEmitidaNoEncontradaError,
)
from app.services.emision_disposicion import (
    EmisionDisposicionError,
    EmisionProveedorOPNoHabilitadoError,
)
from app.repositories.registrar_firma_persistence import (
    DisposicionEmitidaNoEncontradaAlFirmarError,
    EstadoExpedienteIncompatibleParaFirmaError,
    ExpedienteNoEncontradoAlRegistrarFirmaError,
    FechaFirmaAnteriorAEmisionError,
    FirmaYaRegistradaError,
)
from app.services.registro_firma import FechaFirmaFuturaError
from app.repositories.registrar_archivo_persistence import (
    ArchivoYaRegistradoError,
    EstadoExpedienteIncompatibleParaArchivoError,
    ExpedienteNoEncontradoAlRegistrarArchivoError,
    FechaArchivoAnteriorAFirmaError,
    FirmaAusenteOInconsistenteAlArchivarError,
)
from app.services.registro_archivo import FechaArchivoFuturaError
from app.composition.checklist_fisico import checklist_fisico_service
from app.composition.expediente import expediente_service
from app.composition.validacion import validacion_service
from app.services.historial import historial_service
from app.services.parametros import parametros_institucionales_service
from app.services.texto_documento import texto_documento_service

router = APIRouter()


def _eliminar_archivo_guardado(ruta_relativa: str) -> None:
    ruta = Path(__file__).resolve().parents[3] / ruta_relativa
    try:
        ruta.unlink(missing_ok=True)
    except OSError:
        pass


@router.get("/administracion/parametros", response_model=ParametrosInstitucionalesRead)
def obtener_parametros_institucionales():
    return parametros_institucionales_service.obtener()


@router.put("/administracion/parametros", response_model=ParametrosInstitucionalesRead)
def actualizar_parametros_institucionales(data: ParametrosInstitucionalesUpdate):
    return parametros_institucionales_service.actualizar(data)



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
    try:
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
    except Exception:
        _eliminar_archivo_guardado(ruta_relativa)
        raise
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
    obtener_expediente(expediente_id)

    nombre_original, ruta_relativa, tamano_bytes, mime_type = await guardar_upload(expediente_id, file, "op")
    try:
        documento = documento_service.agregar_op(
            expediente_id,
            DocumentoCreate(
                tipo="OP",
                nombre_archivo=nombre_original,
                ruta=ruta_relativa,
                observaciones=(
                    "Orden de Pago cargada desde la ficha "
                    "del expediente."
                ),
                tamano_bytes=tamano_bytes,
                mime_type=mime_type,
            ),
        )
    except Exception:
        _eliminar_archivo_guardado(ruta_relativa)
        raise
    historial_service.registrar(expediente_id, "OP_CARGADA", detalle=documento.nombre_archivo)
    return documento


def _analizar_op_o_conflicto(
    expediente_id: str,
    *,
    reconstruir: bool = False,
) -> AnalisisOPRead:
    try:
        if reconstruir:
            return analisis_op_service.reconstruir(expediente_id)
        return analisis_op_service.analizar(expediente_id)
    except ConfiguracionUCVigenteNoEncontradaError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": str(exc),
                "errores": [
                    "No existe una Configuración UC vigente para analizar "
                    "la Orden de Pago."
                ],
            },
        ) from exc
    except ConfiguracionUCHistoricaNoEncontradaError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": str(exc),
                "errores": [
                    "La referencia histórica de Configuración UC "
                    "no pudo ser recuperada."
                ],
            },
        ) from exc
    except ConfiguracionUCNoAsociadaError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": str(exc),
                "errores": [
                    "Ejecute el análisis de la Orden de Pago para asociar "
                    "la Configuración UC correspondiente."
                ],
            },
        ) from exc


def _verificar_op_legible_para_disposicion(expediente_id: str) -> AnalisisOPRead:
    analisis = _analizar_op_o_conflicto(expediente_id)

    if not analisis.op_detectada:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "No se puede continuar sin una Orden de Pago.",
                "errores": ["Falta cargar la Orden de Pago."],
            },
        )

    if analisis.modo == "EXTRACCION_FALLIDA":
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": (
                    "La Orden de Pago fue incorporada al expediente, pero no "
                    "fue posible extraer la información necesaria para generar "
                    "la disposición."
                ),
                "errores": [
                    "No fue posible leer correctamente el contenido de la Orden "
                    "de Pago."
                ],
            },
        )

    return analisis


@router.post(
    "/{expediente_id}/analizar-op",
    response_model=AnalisisOPRead,
    deprecated=True,
)
def analizar_op(expediente_id: str):
    obtener_expediente(expediente_id)
    if not validacion_service.tiene_op(expediente_id):
        historial_service.registrar(expediente_id, "ANALISIS_OP_BLOQUEADO", detalle="No existe OP cargada.")
    analisis = _analizar_op_o_conflicto(expediente_id)
    if analisis.modo == "EXTRACCION_FALLIDA":
        historial_service.registrar(
            expediente_id,
            "ANALISIS_OP_FALLIDO",
            detalle=(
                "No fue posible leer correctamente el contenido de la Orden "
                "de Pago."
            ),
        )
    else:
        historial_service.registrar(expediente_id, "OP_ANALIZADA_IA", detalle=f"Modo {analisis.modo}")
    return analisis


def _analizar_documento_op_o_error(
    expediente_id: str,
    documento_id: str,
    *,
    reconstruir: bool = False,
) -> AnalisisOPRead:
    try:
        if reconstruir:
            return analisis_op_service.reconstruir_documento(
                expediente_id,
                documento_id,
            )
        return analisis_op_service.analizar_documento(
            expediente_id,
            documento_id,
        )
    except DocumentoOPNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentoOPExpedienteInconsistenteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DocumentoNoEsOPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ArchivoOPNoDisponibleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ArchivoOPNoAnalizableError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfiguracionUCVigenteNoEncontradaError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": str(exc),
                "errores": [
                    "No existe una Configuración UC vigente para analizar "
                    "la Orden de Pago."
                ],
            },
        ) from exc
    except ConfiguracionUCHistoricaNoEncontradaError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": str(exc),
                "errores": [
                    "La referencia histórica de Configuración UC "
                    "no pudo ser recuperada."
                ],
            },
        ) from exc
    except ConfiguracionUCNoAsociadaError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": str(exc),
                "errores": [
                    "Ejecute el análisis explícito de la Orden de Pago "
                    "seleccionada para asociar la Configuración UC."
                ],
            },
        ) from exc


@router.get(
    "/{expediente_id}/analisis-op",
    response_model=AnalisisOPRead,
    deprecated=True,
)
def obtener_analisis_op(expediente_id: str):
    obtener_expediente(expediente_id)
    return _analizar_op_o_conflicto(expediente_id, reconstruir=True)


@router.post(
    "/{expediente_id}/documentos/{documento_id}/analisis-op",
    response_model=AnalisisOPRead,
)
def analizar_documento_op(
    expediente_id: str,
    documento_id: str,
):
    obtener_expediente(expediente_id)
    analisis = _analizar_documento_op_o_error(
        expediente_id,
        documento_id,
    )
    historial_service.registrar(
        expediente_id,
        "OP_ANALIZADA_IA",
        detalle=f"Documento {documento_id} | Modo {analisis.modo}",
    )
    return analisis


@router.get(
    "/{expediente_id}/documentos/{documento_id}/analisis-op",
    response_model=AnalisisOPRead,
)
def obtener_analisis_documento_op(
    expediente_id: str,
    documento_id: str,
):
    obtener_expediente(expediente_id)
    return _analizar_documento_op_o_error(
        expediente_id,
        documento_id,
        reconstruir=True,
    )


def _controlar_proveedor_op_o_error(
    expediente_id: str,
    documento_id: str,
    *,
    reconstruir: bool = False,
) -> ControlProveedorOPRead:
    try:
        if reconstruir:
            return control_proveedor_op_service.consultar(
                expediente_id,
                documento_id,
            )
        return control_proveedor_op_service.ejecutar(
            expediente_id,
            documento_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Expediente no encontrado",
        ) from exc
    except DocumentoOPNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentoOPExpedienteInconsistenteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DocumentoNoEsOPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ArchivoOPNoDisponibleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ArchivoOPNoAnalizableError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfiguracionUCVigenteNoEncontradaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ConfiguracionUCHistoricaNoEncontradaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ConfiguracionUCNoAsociadaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _registrar_control_proveedor_op_o_error(
    expediente_id: str,
    documento_id: str,
) -> ControlProveedorOPRegistroRead:
    try:
        return registrar_control_proveedor_op_service.ejecutar(
            expediente_id,
            documento_id,
        )
    except SeleccionControlObsoletaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Expediente no encontrado",
        ) from exc
    except DocumentoOPNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentoOPExpedienteInconsistenteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DocumentoNoEsOPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ArchivoOPNoDisponibleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ArchivoOPNoAnalizableError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfiguracionUCVigenteNoEncontradaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ConfiguracionUCHistoricaNoEncontradaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ConfiguracionUCNoAsociadaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    (
        "/{expediente_id}/documentos/{documento_id}"
        "/control-proveedor"
    ),
    response_model=ControlProveedorOPRegistroRead,
)
def ejecutar_control_proveedor_op(
    expediente_id: str,
    documento_id: str,
    response: Response,
):
    resultado = _registrar_control_proveedor_op_o_error(
        expediente_id,
        documento_id,
    )
    response.status_code = (
        201 if resultado.id_control is not None else 200
    )
    return resultado


@router.get(
    (
        "/{expediente_id}/documentos/{documento_id}"
        "/control-proveedor"
    ),
    response_model=ControlProveedorOPRead,
)
def consultar_control_proveedor_op(
    expediente_id: str,
    documento_id: str,
):
    return _controlar_proveedor_op_o_error(
        expediente_id,
        documento_id,
        reconstruir=True,
    )


@router.get(
    (
        "/{expediente_id}/documentos/{documento_id}"
        "/habilitacion-proveedor"
    ),
    response_model=HabilitacionProveedorOPRead,
)
def consultar_habilitacion_proveedor_op(
    expediente_id: str,
    documento_id: str,
):
    try:
        return evaluar_habilitacion_proveedor_op_service.evaluar(
            expediente_id,
            documento_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Expediente no encontrado",
        ) from exc
    except DocumentoOPNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentoOPExpedienteInconsistenteError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except DocumentoNoEsOPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
    resultado = validacion_service.validar(expediente_id)

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

    expediente = validacion_service.registrar(
        validacion_calculada=resultado,
        resultado="VALIDADA",
        usuario="Secretario Técnico",
    )
    historial_service.registrar(expediente_id, "EXPEDIENTE_VALIDADO")
    return expediente


@router.post("/{expediente_id}/validar-con-observaciones", response_model=ExpedienteRead)
def validar_expediente_con_observaciones(expediente_id: str, data: ValidacionObservadaCreate):
    obtener_expediente(expediente_id)
    resultado = validacion_service.validar(expediente_id)

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

    expediente = validacion_service.registrar(
        validacion_calculada=resultado,
        resultado="VALIDADA_CON_OBSERVACIONES",
        usuario=data.usuario,
        motivo_observacion=data.motivo,
    )
    historial_service.registrar(
        expediente_id,
        "EXPEDIENTE_VALIDADO_CON_OBSERVACIONES",
        usuario=data.usuario,
        detalle=detalle,
    )
    return expediente


def _traducir_error_borrador(exc: Exception) -> HTTPException:
    if isinstance(exc, BorradorDisposicionNoHabilitadoError):
        return HTTPException(
            status_code=409,
            detail={
                "estado": exc.estado.value,
                "mensaje": exc.mensaje,
                "proxima_accion": exc.proxima_accion,
                "documento_op_id": exc.documento_op_id,
            },
        )
    if isinstance(exc, BorradorDisposicionObsoletoError):
        return HTTPException(
            status_code=409,
            detail={
                "mensaje": exc.mensaje,
                "documento_op_id": exc.documento_op_id,
            },
        )
    if isinstance(exc, DisposicionOPNoEncontradaError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DisposicionOPAmbiguaError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DocumentoOPNoEncontradoError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DocumentoOPExpedienteInconsistenteError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DocumentoNoEsOPError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


def _texto_borrador(borrador: DisposicionRead) -> str:
    return (
        f"DISPOSICIÓN Nº {borrador.numero_disposicion or '____/____'}\n\n"
        f"VISTO:\n{borrador.visto}\n\n"
        f"CONSIDERANDO:\n{borrador.considerando}\n\n"
        f"{borrador.dispone}\n\n"
        "OBSERVACIONES IA\n"
        + "\n".join(f"- {obs}" for obs in borrador.observaciones_ia)
    )


@router.post(
    "/{expediente_id}/disposicion/borrador",
    response_model=DisposicionRead,
    deprecated=True,
)
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
    try:
        return disposicion_service.generar_borrador_legacy(
            expediente_id, regenerar=regenerar
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc


@router.get(
    "/{expediente_id}/disposicion/borrador",
    response_model=DisposicionRead,
    deprecated=True,
)
def obtener_borrador_disposicion(expediente_id: str):
    obtener_expediente(expediente_id)
    try:
        return disposicion_service.obtener(expediente_id)
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc


@router.put(
    "/{expediente_id}/disposicion/borrador",
    response_model=DisposicionRead,
    deprecated=True,
)
def actualizar_borrador_disposicion(expediente_id: str, data: DisposicionUpdate):
    obtener_expediente(expediente_id)
    try:
        return disposicion_service.actualizar_borrador_legacy(
            expediente_id, data
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc







@router.get("/{expediente_id}/disposicion/borrador/docx", deprecated=True)
def descargar_borrador_disposicion_docx(expediente_id: str):
    obtener_expediente(expediente_id)
    try:
        ruta = disposicion_docx_service.generar_docx(expediente_id)
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc
    return FileResponse(
        path=ruta,
        filename=ruta.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{expediente_id}/disposicion/borrador/texto", deprecated=True)
def exportar_borrador_disposicion_texto(expediente_id: str):
    obtener_expediente(expediente_id)
    try:
        borrador = disposicion_service.obtener(expediente_id)
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc
    contenido = _texto_borrador(borrador)
    return PlainTextResponse(contenido, media_type="text/plain; charset=utf-8")


@router.post(
    "/{expediente_id}/documentos/{documento_id}/disposicion/borrador",
    response_model=DisposicionRead,
)
def generar_borrador_disposicion_documento(
    expediente_id: str, documento_id: str, regenerar: bool = False
):
    obtener_expediente(expediente_id)
    try:
        return disposicion_service.generar_borrador(
            expediente_id, documento_id, regenerar=regenerar
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc


@router.get(
    "/{expediente_id}/documentos/{documento_id}/disposicion/borrador",
    response_model=DisposicionRead,
)
def obtener_borrador_disposicion_documento(
    expediente_id: str, documento_id: str
):
    obtener_expediente(expediente_id)
    try:
        return disposicion_service.obtener_borrador(
            expediente_id, documento_id
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc


@router.put(
    "/{expediente_id}/documentos/{documento_id}/disposicion/borrador",
    response_model=DisposicionRead,
)
def actualizar_borrador_disposicion_documento(
    expediente_id: str, documento_id: str, data: DisposicionUpdate
):
    obtener_expediente(expediente_id)
    try:
        return disposicion_service.actualizar_borrador(
            expediente_id, documento_id, data
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc


@router.get(
    "/{expediente_id}/documentos/{documento_id}/disposicion/borrador/docx"
)
def descargar_borrador_disposicion_documento_docx(
    expediente_id: str, documento_id: str
):
    obtener_expediente(expediente_id)
    try:
        ruta = disposicion_docx_service.generar_docx(
            expediente_id, documento_id
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc
    return FileResponse(
        path=ruta,
        filename=ruta.name,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )


@router.get(
    "/{expediente_id}/documentos/{documento_id}/disposicion/borrador/texto"
)
def exportar_borrador_disposicion_documento_texto(
    expediente_id: str, documento_id: str
):
    obtener_expediente(expediente_id)
    try:
        borrador = disposicion_service.obtener_borrador(
            expediente_id, documento_id
        )
    except Exception as exc:
        raise _traducir_error_borrador(exc) from exc
    return PlainTextResponse(
        _texto_borrador(borrador),
        media_type="text/plain; charset=utf-8",
    )


@router.post(
    "/{expediente_id}/generar-disposicion",
    response_model=ExpedienteRead,
    deprecated=True,
)
def generar_disposicion(expediente_id: str):
    try:
        disposicion = emision_disposicion_service.emitir(expediente_id)
    except ExpedienteNoEncontradoAlEmitirError as exc:
        raise HTTPException(
            status_code=404,
            detail="Expediente no encontrado",
        ) from exc
    except (
        DisposicionYaRegistradaError,
        EstadoExpedienteIncompatibleError,
    ) as exc:
        historial_service.registrar(
            expediente_id,
            "GENERACION_DISPOSICION_BLOQUEADA",
            detalle=str(exc),
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EmisionDisposicionError as exc:
        historial_service.registrar(
            expediente_id,
            "GENERACION_DISPOSICION_BLOQUEADA",
            detalle=str(exc),
        )
        if exc.habilitacion is None:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(
            status_code=409,
            detail={
                "habilitada": False,
                "motivos": [
                    {
                        "codigo": motivo.codigo,
                        "descripcion": motivo.descripcion,
                    }
                    for motivo in exc.habilitacion.motivos
                ],
            },
        ) from exc
    historial_service.registrar(expediente_id, "DISPOSICION_GENERADA")
    return disposicion


@router.post(
    "/{expediente_id}/documentos/{documento_id}/disposicion",
    response_model=DisposicionEmitidaRead,
    status_code=201,
)
def emitir_disposicion_documento(
    expediente_id: str,
    documento_id: str,
    data: DisposicionEmitirCreate,
):
    try:
        resultado = emision_disposicion_service.emitir(
            expediente_id,
            documento_id,
            data.numero_disposicion,
        )
    except ExpedienteNoEncontradoAlEmitirError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentoOPNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentoNoEsOPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (
        DocumentoOPExpedienteInconsistenteError,
        DisposicionYaRegistradaError,
        EstadoExpedienteIncompatibleError,
        ContextoEmisionObsoletoError,
        BorradorDisposicionObsoletoError,
        EmisionDisposicionError,
        EmisionProveedorOPNoHabilitadoError,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    historial_service.registrar(
        expediente_id,
        "DISPOSICION_GENERADA",
        detalle=(
            f"Documento OP: {documento_id} | "
            f"Disposición: {resultado.numero_disposicion}"
        ),
    )
    return resultado


@router.get(
    "/{expediente_id}/documentos/{documento_id}/disposicion",
    response_model=DisposicionEmitidaRead,
)
def obtener_disposicion_emitida_documento(
    expediente_id: str,
    documento_id: str,
):
    try:
        return consulta_disposicion_service.obtener_por_documento_op(
            expediente_id, documento_id
        )
    except DisposicionEmitidaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{expediente_id}/disposicion",
    response_model=DisposicionEmitidaRead,
    deprecated=True,
)
def obtener_disposicion_emitida(expediente_id: str):
    try:
        return consulta_disposicion_service.obtener_por_expediente(
            expediente_id
        )
    except DisposicionEmitidaNoEncontradaError as exc:
        raise HTTPException(
            status_code=404,
            detail="Disposición emitida no encontrada",
        ) from exc


@router.post(
    "/{expediente_id}/registrar-firma",
    response_model=ExpedienteRead,
)
def registrar_firma(
    expediente_id: str,
    data: RegistroFirmaCreate,
):
    try:
        return registro_firma_service.registrar(
            expediente_id,
            data.fecha_firma,
        )
    except ExpedienteNoEncontradoAlRegistrarFirmaError as exc:
        raise HTTPException(
            status_code=404,
            detail="Expediente no encontrado",
        ) from exc
    except (
        EstadoExpedienteIncompatibleParaFirmaError,
        FirmaYaRegistradaError,
        DisposicionEmitidaNoEncontradaAlFirmarError,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (
        FechaFirmaFuturaError,
        FechaFirmaAnteriorAEmisionError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/{expediente_id}/registrar-archivo",
    response_model=ExpedienteRead,
)
def registrar_archivo(
    expediente_id: str,
    data: RegistroArchivoCreate,
):
    try:
        return registro_archivo_service.registrar(
            expediente_id,
            data.fecha_archivo,
        )
    except ExpedienteNoEncontradoAlRegistrarArchivoError as exc:
        raise HTTPException(
            status_code=404,
            detail="Expediente no encontrado",
        ) from exc
    except (
        EstadoExpedienteIncompatibleParaArchivoError,
        ArchivoYaRegistradoError,
        FirmaAusenteOInconsistenteAlArchivarError,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (
        FechaArchivoFuturaError,
        FechaArchivoAnteriorAFirmaError,
    ) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{expediente_id}/historial", response_model=list[HistorialRead])
def listar_historial(expediente_id: str):
    obtener_expediente(expediente_id)
    return historial_service.listar_por_expediente(expediente_id)
