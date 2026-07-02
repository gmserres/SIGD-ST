
from datetime import datetime
from pathlib import Path
import re

from app.modules.documentos.extractor_datos import extraer_datos_op_desde_pdf
from app.schemas.disposicion import DisposicionRead, DisposicionUpdate
from app.services.analisis_op import analisis_op_service
from app.services.documentos import documento_service
from app.services.expedientes import expediente_service
from app.services.historial import historial_service
from app.services.template_engine import (
    dividir_disposicion,
    formatear_moneda,
    formatear_numero,
    numero_a_letras,
    template_engine,
)


class DisposicionService:
    def __init__(self) -> None:
        self._borradores: dict[str, DisposicionRead] = {}
        self._plantilla_fc = Path(__file__).resolve().parents[3] / "storage" / "templates" / "disposicion_fc_v2026.md"

    def generar_borrador(self, expediente_id: str, regenerar: bool = False) -> DisposicionRead:
        if expediente_id in self._borradores and not regenerar:
            return self._borradores[expediente_id]

        expediente = expediente_service.obtener(expediente_id)
        analisis = analisis_op_service.analizar(expediente_id)
        historial = historial_service.listar_por_expediente(expediente_id)
        validado_observado = any(h.accion == "EXPEDIENTE_VALIDADO_CON_OBSERVACIONES" for h in historial)
        checklist_fisico = any(h.accion == "CHECKLIST_FISICO_REGISTRADO" for h in historial)
        datos_op = self._datos_op(expediente_id)

        plantilla = template_engine.cargar(self._plantilla_fc)
        variables = self._construir_variables(expediente, analisis, datos_op)
        render = template_engine.renderizar(plantilla, variables)
        visto, considerando, dispone = dividir_disposicion(render.contenido)

        numero = expediente.numero_disposicion or "____/____"
        observaciones = [
            "Borrador generado con motor de plantillas institucionales.",
            "Plantilla: disposicion_fc_v2026.md.",
            f"Variables reemplazadas: {len(render.variables_usadas) - len(render.variables_faltantes)} de {len(render.variables_usadas)}.",
        ]
        if render.variables_faltantes:
            observaciones.append("Variables pendientes: " + ", ".join(render.variables_faltantes))
        if checklist_fisico:
            observaciones.append("La documentación física fue acreditada mediante checklist de validación.")
        if validado_observado:
            observaciones.append("El expediente fue validado con observaciones. Revisar el historial antes de emitir.")

        ahora = datetime.now()
        borrador = DisposicionRead(
            expediente_id=expediente_id,
            numero_disposicion=numero,
            estado="BORRADOR_PLANTILLA",
            visto=visto,
            considerando=considerando,
            dispone=dispone,
            observaciones_ia=observaciones,
            creado=ahora,
            actualizado=ahora,
        )
        self._borradores[expediente_id] = borrador
        historial_service.registrar(
            expediente_id,
            "PLANTILLA_APLICADA",
            detalle=f"Disposición FC 2026 | variables: {len(render.variables_usadas) - len(render.variables_faltantes)}/{len(render.variables_usadas)}",
        )
        historial_service.registrar(expediente_id, "BORRADOR_DISPOSICION_GENERADO", detalle=f"Borrador de Disposición Nº {numero}")
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

    def _datos_op(self, expediente_id: str):
        documentos = documento_service.listar_por_expediente(expediente_id)
        op = next((doc for doc in documentos if doc.tipo == "OP"), None)
        if not op:
            return None
        ruta = Path(__file__).resolve().parents[3] / op.ruta
        if not ruta.exists():
            return None
        return extraer_datos_op_desde_pdf(ruta)

    def _construir_variables(self, expediente, analisis, datos_op) -> dict[str, str]:
        importe_bruto = analisis.importe_bruto
        fecha = self._fecha_larga(analisis.fecha_op)
        ejercicio = self._ejercicio(analisis.fecha_op)
        facturas = datos_op.facturas if datos_op else analisis.documentos_comerciales
        retenciones = datos_op.retenciones if datos_op else analisis.retenciones
        texto_op = datos_op.texto_extraido if datos_op else ""
        forma_pago = self._extraer_por_etiqueta(texto_op, "Forma de Pago") or "Transferencia"
        cbu = self._extraer_por_etiqueta(texto_op, "Número de cbu") or self._extraer_por_etiqueta(texto_op, "Numero de cbu") or "CBU pendiente de verificación"
        fondo = (datos_op.fondo if datos_op and datos_op.fondo else analisis.fondo) or "FONDO COMPENSADOR"
        fondo = fondo.upper()
        articulo_dr = self._articulo_dr(analisis.procedimiento)

        return {
            "FECHA": fecha,
            "EXPEDIENTE": expediente.numero_interno,
            "DISPOSICION": expediente.numero_disposicion or "____/____",
            "PROVEEDOR": analisis.proveedor or "PROVEEDOR PENDIENTE",
            "CUIT": analisis.cuit or "CUIT PENDIENTE",
            "IMPORTE": formatear_moneda(importe_bruto),
            "IMPORTE_LETRAS": numero_a_letras(importe_bruto),
            "UC": formatear_numero(analisis.cantidad_uc, 2),
            "NORMA_UC": analisis.norma_uc,
            "TABLA_FACTURAS": self._tabla_facturas(facturas),
            "CONCEPTO_PAGO": expediente.objeto or "concepto pendiente de completar",
            "ESTABLECIMIENTOS": expediente.establecimiento or "establecimientos pendientes de completar",
            "ARTICULO_DR": articulo_dr,
            "PROCEDIMIENTO": analisis.procedimiento or "procedimiento pendiente",
            "TABLA_DETALLE_OP": self._tabla_detalle_op(importe_bruto, retenciones, analisis.importe_neto, forma_pago, cbu),
            "FONDO": fondo,
            "EJERCICIO": ejercicio,
        }

    def _tabla_facturas(self, facturas) -> str:
        if not facturas:
            return "Factura | Fecha | Importe\n--- | --- | ---\nFactura pendiente | Fecha pendiente | Importe pendiente"
        filas = ["Factura | Fecha | Importe", "--- | --- | ---"]
        for factura in facturas:
            codigo = self._codigo_factura(factura)
            filas.append(f"{codigo} | {factura.fecha} | {formatear_moneda(factura.importe)}")
        return "\n".join(filas)

    def _tabla_detalle_op(self, importe_bruto, retenciones, importe_neto, forma_pago: str, cbu: str) -> str:
        filas = ["Concepto | Detalle", "--- | ---"]
        filas.append(f"Monto Total de Facturas | {formatear_moneda(importe_bruto)}")
        for retencion in retenciones:
            filas.append(f"{retencion.concepto} | {formatear_moneda(retencion.importe)}")
        filas.append(f"**Monto Neto a Pagar** | **{formatear_moneda(importe_neto)}**")
        filas.append(f"Forma de Pago | {forma_pago}")
        filas.append(f"Número de CBU | {cbu}")
        return "\n".join(filas)

    def _codigo_factura(self, factura) -> str:
        letra = getattr(factura, "letra", "") or ""
        numero = getattr(factura, "numero", "") or ""
        if numero.startswith("FAC"):
            return numero
        return f"FAC[{letra}]{numero}" if letra else numero

    def _fecha_larga(self, fecha: str | None) -> str:
        if not fecha:
            return datetime.now().strftime("%d de %m de %Y")
        partes = re.split(r"[/-]", fecha)
        if len(partes) != 3:
            return fecha
        dia = int(partes[0])
        mes = int(partes[1])
        anio = partes[2]
        meses = [
            "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        return f"{dia} de {meses[mes]} de {anio}"

    def _ejercicio(self, fecha: str | None) -> str:
        if fecha:
            partes = re.split(r"[/-]", fecha)
            if len(partes) == 3:
                return partes[2]
        return str(datetime.now().year)

    def _articulo_dr(self, procedimiento: str | None) -> str:
        if procedimiento == "Factura Conformada":
            return "18 inc. C"
        return "artículo pendiente de parametrización"

    def _extraer_por_etiqueta(self, texto: str, etiqueta: str) -> str | None:
        if not texto:
            return None
        patron = rf"{re.escape(etiqueta)}\s*[:.\- ]*(?:\.|\s)*(.+)"
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if not match:
            return None
        valor = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
        return valor[:120] if valor else None


disposicion_service = DisposicionService()
