from datetime import datetime

from app.schemas.disposicion import DisposicionRead, DisposicionUpdate
from app.services.analisis_op import analisis_op_service
from app.services.expedientes import expediente_service
from app.services.historial import historial_service


class DisposicionService:
    def __init__(self) -> None:
        self._borradores: dict[str, DisposicionRead] = {}

    def generar_borrador(self, expediente_id: str, regenerar: bool = False) -> DisposicionRead:
        if expediente_id in self._borradores and not regenerar:
            return self._borradores[expediente_id]

        expediente = expediente_service.obtener(expediente_id)
        analisis = analisis_op_service.analizar(expediente_id)
        historial = historial_service.listar_por_expediente(expediente_id)
        validado_observado = any(h.accion == "EXPEDIENTE_VALIDADO_CON_OBSERVACIONES" for h in historial)

        numero = expediente.numero_disposicion or "____/____"
        proveedor = analisis.proveedor or "el proveedor identificado en las actuaciones"
        cuit = analisis.cuit or "CUIT pendiente de verificación"
        objeto = expediente.objeto or "el objeto indicado en las actuaciones"
        expediente_numero = expediente.numero_interno
        establecimiento = expediente.establecimiento or "los establecimientos educativos correspondientes"
        importe = self._formatear_moneda(analisis.importe_bruto)
        op = analisis.orden_pago or "la Orden de Pago agregada"
        procedimiento = analisis.procedimiento or "el procedimiento administrativo correspondiente"

        visto = (
            f"VISTO el Expediente Nº {expediente_numero}, mediante el cual se tramita {objeto}, "
            f"correspondiente a {establecimiento};"
        )

        considerando_partes = [
            f"Que obra agregada la Orden de Pago {op}, vinculada al proveedor {proveedor}, CUIT {cuit};",
            f"Que del análisis documental surge un importe total de {importe}, encuadrado preliminarmente como {procedimiento};",
            "Que la documentación incorporada al expediente fue evaluada mediante el sistema SIGD-ST, sin perjuicio de la revisión administrativa que corresponda;",
        ]

        if analisis.documentos_comerciales:
            considerando_partes.append(
                f"Que se detectaron {len(analisis.documentos_comerciales)} factura(s) liquidadas asociadas a la Orden de Pago, resultando consistente la información económica analizada;"
            )

        if validado_observado:
            considerando_partes.append(
                "Que el expediente fue validado con observaciones, constando la justificación correspondiente en el historial de actuaciones;"
            )

        considerando_partes.append(
            "Que corresponde dictar el presente acto administrativo en el marco de las competencias del Consejo Escolar;"
        )

        considerando = "\n\n".join(considerando_partes)

        dispone = (
            "EL CUERPO DE CONSEJEROS ESCOLARES DE GRAL. ALVARADO DISPONE\n\n"
            f"ARTÍCULO 1°: Aprobar la tramitación correspondiente al Expediente Nº {expediente_numero}, "
            f"por el objeto: {objeto}.\n\n"
            f"ARTÍCULO 2°: Autorizar la prosecución del trámite administrativo vinculado a la Orden de Pago {op}, "
            f"por el importe de {importe}, a favor de {proveedor}.\n\n"
            "ARTÍCULO 3°: Registrar, comunicar a las áreas intervinientes y archivar oportunamente."
        )

        observaciones = [
            "Borrador generado automáticamente por SIGD-ST.",
            "Revisar datos de expediente, proveedor, importe y objeto antes de emitir.",
        ]

        if validado_observado:
            observaciones.append("El expediente fue validado con observaciones. Revisar el historial antes de emitir.")

        if analisis.faltantes:
            observaciones.append("Existen evidencias o documentos pendientes de acreditación según el análisis IA.")

        ahora = datetime.now()
        borrador = DisposicionRead(
            expediente_id=expediente_id,
            numero_disposicion=numero,
            estado="BORRADOR_IA",
            visto=visto,
            considerando=considerando,
            dispone=dispone,
            observaciones_ia=observaciones,
            creado=ahora,
            actualizado=ahora,
        )
        self._borradores[expediente_id] = borrador
        historial_service.registrar(expediente_id, "BORRADOR_DISPOSICION_GENERADO", detalle=f"Disposición {numero}")
        return borrador

    def actualizar_borrador(self, expediente_id: str, data: DisposicionUpdate) -> DisposicionRead:
        borrador = self.generar_borrador(expediente_id)
        actualizado = borrador.model_copy(
            update={
                **data.model_dump(exclude_unset=True),
                "actualizado": datetime.now(),
            }
        )
        self._borradores[expediente_id] = actualizado
        historial_service.registrar(expediente_id, "BORRADOR_DISPOSICION_ACTUALIZADO")
        return actualizado

    def obtener(self, expediente_id: str) -> DisposicionRead:
        return self.generar_borrador(expediente_id)

    @staticmethod
    def _formatear_moneda(valor: float | None) -> str:
        if valor is None:
            return "importe pendiente de verificación"
        entero, decimales = f"{valor:.2f}".split(".")
        partes = []
        while entero:
            partes.insert(0, entero[-3:])
            entero = entero[:-3]
        return "$ " + ".".join(partes) + "," + decimales


disposicion_service = DisposicionService()
