from app.domain.estados import EstadoExpediente
from app.schemas.validacion import ControlValidacion, ValidacionExpedienteRead
from app.services.documentos import documento_service
from app.services.expedientes import expediente_service
from app.services.historial import historial_service
from app.services.checklist_fisico import checklist_fisico_service


class ValidacionService:
    def validar(self, expediente_id: str, registrar_historial: bool = True) -> ValidacionExpedienteRead:
        expediente = expediente_service.obtener(expediente_id)
        documentos = documento_service.listar_por_expediente(expediente_id)
        checklist = checklist_fisico_service.obtener(expediente_id)

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

        agregar("Expediente interno", bool(expediente.numero_interno), "Expediente informado.", "Falta número de expediente interno.")
        agregar("Número de disposición", bool(expediente.numero_disposicion), "Número de disposición informado.", "Falta número de disposición.")
        agregar("Establecimiento", bool(expediente.establecimiento), "Establecimiento informado.", "Falta establecimiento.")
        agregar("Objeto", bool(expediente.objeto), "Objeto informado.", "Falta objeto de la contratación.")

        tipos = {doc.tipo.upper() for doc in documentos}
        tiene_op = "OP" in tipos
        agregar("Orden de Pago", tiene_op, "OP cargada.", "Falta cargar la Orden de Pago.")

        factura_acreditada = "FACTURA" in tipos or "CHECK_FACTURA" in tipos or bool(checklist and checklist.factura)
        agregar(
            "Facturas",
            factura_acreditada or tiene_op,
            "Facturas acreditadas por archivo, checklist o facturas liquidadas en OP.",
            "Falta acreditar facturas por archivo o checklist.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Remito o conformidad",
            bool({"REMITO", "CONFORMIDAD", "ACTA_RECEPCION", "CHECK_REMITO"} & tipos) or bool(checklist and checklist.remito_conformidad),
            "Remito, conformidad o acta acreditada.",
            "Falta acreditar remito, conformidad o acta de recepción.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Validación CAE",
            "CAE" in tipos or "VALIDACION_CAE" in tipos or "CHECK_CAE" in tipos or bool(checklist and checklist.cae),
            "CAE acreditado.",
            "Falta acreditar validación CAE.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Constancia ARCA",
            "ARCA" in tipos or "CHECK_ARCA" in tipos or bool(checklist and checklist.arca),
            "Constancia ARCA acreditada.",
            "Falta acreditar constancia ARCA.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Certificado ARBA",
            "ARBA" in tipos or "CHECK_ARBA" in tipos or bool(checklist and checklist.arba),
            "Certificado ARBA acreditado.",
            "Falta acreditar certificado fiscal ARBA.",
            severidad="ADVERTENCIA",
        )

        controles.append(
            ControlValidacion(
                control="Estado para generar disposición",
                estado="OK" if expediente.estado == EstadoExpediente.VALIDADO else "ADVERTENCIA",
                observacion="El expediente está validado." if expediente.estado == EstadoExpediente.VALIDADO else "El expediente será validable si no existen errores ni advertencias documentales.",
            )
        )

        estado_general = "ROJO" if errores else ("AMARILLO" if advertencias else "VERDE")

        if registrar_historial:
            historial_service.registrar(expediente_id, "VALIDACION_CONSULTADA", detalle=f"Estado general: {estado_general}")

        return ValidacionExpedienteRead(
            expediente_id=expediente_id,
            estado_general=estado_general,
            errores=errores,
            advertencias=advertencias,
            controles=controles,
        )

    def errores_bloqueantes(self, expediente_id: str) -> list[str]:
        return self.validar(expediente_id, registrar_historial=False).errores

    def advertencias_validacion(self, expediente_id: str) -> list[str]:
        return self.validar(expediente_id, registrar_historial=False).advertencias

    def puede_validar_normal(self, expediente_id: str) -> bool:
        resultado = self.validar(expediente_id, registrar_historial=False)
        return not resultado.errores and not resultado.advertencias

    def puede_validar_con_observaciones(self, expediente_id: str) -> bool:
        resultado = self.validar(expediente_id, registrar_historial=False)
        return not resultado.errores and bool(resultado.advertencias)

    def tiene_op(self, expediente_id: str) -> bool:
        documentos = documento_service.listar_por_expediente(expediente_id)
        return any(doc.tipo == "OP" for doc in documentos)


validacion_service = ValidacionService()
