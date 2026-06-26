from app.domain.estados import EstadoExpediente
from app.schemas.validacion import ControlValidacion, ValidacionExpedienteRead
from app.services.documentos import documento_service
from app.services.expedientes import expediente_service
from app.services.historial import historial_service


class ValidacionService:
    def validar(self, expediente_id: str) -> ValidacionExpedienteRead:
        expediente = expediente_service.obtener(expediente_id)
        documentos = documento_service.listar_por_expediente(expediente_id)

        errores: list[str] = []
        advertencias: list[str] = []
        controles: list[ControlValidacion] = []

        def agregar(control: str, ok: bool, observacion_ok: str, observacion_error: str, severidad: str = "ERROR"):
            if ok:
                controles.append(ControlValidacion(control=control, estado="OK", observacion=observacion_ok))
                return

            controles.append(ControlValidacion(control=control, estado=severidad, observacion=observacion_error))
            if severidad == "ERROR":
                errores.append(observacion_error)
            else:
                advertencias.append(observacion_error)

        agregar(
            "Expediente interno",
            bool(expediente.numero_interno),
            "Expediente informado.",
            "Falta número de expediente interno.",
        )

        agregar(
            "Número de disposición",
            bool(expediente.numero_disposicion),
            "Número de disposición informado.",
            "Falta número de disposición.",
        )

        agregar(
            "Establecimiento",
            bool(expediente.establecimiento),
            "Establecimiento informado.",
            "Falta establecimiento.",
        )

        agregar(
            "Objeto",
            bool(expediente.objeto),
            "Objeto informado.",
            "Falta objeto de la contratación.",
        )

        tiene_op = any(doc.tipo == "OP" for doc in documentos)
        agregar(
            "Orden de Pago",
            tiene_op,
            "OP cargada.",
            "Falta cargar la Orden de Pago.",
        )

        agregar(
            "Documentos complementarios",
            len(documentos) > 1,
            "Existen documentos complementarios.",
            "No se cargaron documentos complementarios. Revisión humana requerida.",
            severidad="ADVERTENCIA",
        )

        puede_generar = expediente.estado == EstadoExpediente.VALIDADO
        agregar(
            "Estado para generar disposición",
            puede_generar,
            "El expediente está validado.",
            "El expediente aún no está validado.",
            severidad="ADVERTENCIA",
        )

        estado_general = "ROJO" if errores else ("AMARILLO" if advertencias else "VERDE")

        historial_service.registrar(
            expediente_id,
            "VALIDACION_CONSULTADA",
            detalle=f"Estado general: {estado_general}",
        )

        return ValidacionExpedienteRead(
            expediente_id=expediente_id,
            estado_general=estado_general,
            errores=errores,
            advertencias=advertencias,
            controles=controles,
        )


validacion_service = ValidacionService()
