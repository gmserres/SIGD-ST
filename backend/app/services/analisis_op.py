from pathlib import Path

from app.modules.documentos.extractor_datos import extraer_datos_op_desde_pdf
from app.modules.fondo_compensador.reglas import (
    NORMA_UC,
    VALOR_UC_VIGENTE,
    calcular_uc,
    determinar_procedimiento,
    encuadre_legal,
)
from app.schemas.analisis_op import AnalisisOPRead, DocumentoComercialExtraido, RetencionExtraida
from app.services.documentos import documento_service


class AnalisisOPService:
    def analizar(self, expediente_id: str) -> AnalisisOPRead:
        documentos = documento_service.listar_por_expediente(expediente_id)
        op = next((doc for doc in documentos if doc.tipo == "OP"), None)

        if op is None:
            return AnalisisOPRead(
                expediente_id=expediente_id,
                modo="ALFA_PDF_TEXTO",
                op_detectada=False,
                proveedor=None,
                cuit=None,
                fondo=None,
                orden_pago=None,
                liquidacion=None,
                fecha_op=None,
                importe_bruto=None,
                importe_neto=None,
                valor_uc=VALOR_UC_VIGENTE,
                norma_uc=NORMA_UC,
                cantidad_uc=None,
                procedimiento=None,
                encuadre_legal=None,
                documentos_comerciales=[],
                retenciones=[],
                validaciones=[],
                advertencias=["No existe Orden de Pago cargada en el expediente."],
                faltantes=["Orden de Pago"],
            )

        ruta = Path(__file__).resolve().parents[3] / op.ruta
        datos = extraer_datos_op_desde_pdf(ruta)

        if datos.texto_extraido:
            importe_bruto = datos.monto_total_facturas or datos.importe_pago or datos.importe_probable
            importe_neto = datos.monto_neto_pagar or datos.importe_pago
            cantidad_uc = calcular_uc(importe_bruto) if importe_bruto else None
            procedimiento = determinar_procedimiento(cantidad_uc) if cantidad_uc else None

            documentos_comerciales = [
                DocumentoComercialExtraido(
                    tipo=factura.tipo,
                    letra=factura.letra,
                    numero=factura.numero,
                    fecha=factura.fecha,
                    importe=factura.importe,
                )
                for factura in datos.facturas
            ]

            retenciones = [
                RetencionExtraida(concepto=ret.concepto, importe=ret.importe)
                for ret in datos.retenciones
            ]

            validaciones = [
                "OP cargada y asociada al expediente.",
                f"Texto extraído del PDF ({datos.paginas} página/s).",
            ]

            faltantes = [
                "Factura",
                "Remito o conformidad firmada",
                "Validación CAE",
                "Certificado Fiscal ARBA",
                "Constancia ARCA",
            ]

            if datos.cuit:
                validaciones.append("CUIT detectado en la OP.")
            else:
                faltantes.append("CUIT no detectado")

            if datos.proveedor:
                validaciones.append("Proveedor probable detectado.")
            else:
                faltantes.append("Proveedor no detectado")

            if datos.monto_total_facturas:
                validaciones.append("Monto total de facturas detectado.")
            elif datos.importe_pago:
                validaciones.append("Importe de pago detectado.")
            else:
                faltantes.append("Importe no detectado")

            if datos.monto_neto_pagar:
                validaciones.append("Monto neto a pagar detectado.")

            if datos.facturas:
                suma_facturas = round(sum(f.importe for f in datos.facturas), 2)
                validaciones.append(f"{len(datos.facturas)} factura(s) liquidadas detectadas.")

                if datos.monto_total_facturas is not None:
                    diferencia = round(abs(suma_facturas - datos.monto_total_facturas), 2)
                    if diferencia <= 1:
                        validaciones.append("La suma de facturas coincide con el monto total.")
                    else:
                        faltantes.append(f"Revisar diferencia entre facturas y monto total: ${diferencia:,.2f}")

            if datos.retenciones:
                validaciones.append(f"{len(datos.retenciones)} retención(es) detectada(s).")

            if cantidad_uc:
                validaciones.append("UC calculadas desde el monto total detectado.")

            advertencias = list(datos.advertencias)
            advertencias.append("Extracción automática inicial. Requiere revisión humana.")

            return AnalisisOPRead(
                expediente_id=expediente_id,
                modo="ALFA_PDF_TEXTO",
                op_detectada=True,
                proveedor=datos.proveedor,
                cuit=datos.cuit,
                fondo=datos.fondo or "Fondo Compensador",
                orden_pago=datos.orden_pago,
                liquidacion=datos.liquidacion,
                fecha_op=datos.fecha,
                importe_bruto=importe_bruto,
                importe_neto=importe_neto,
                valor_uc=VALOR_UC_VIGENTE,
                norma_uc=NORMA_UC,
                cantidad_uc=cantidad_uc,
                procedimiento=procedimiento,
                encuadre_legal=encuadre_legal(procedimiento) if procedimiento else None,
                documentos_comerciales=documentos_comerciales,
                retenciones=retenciones,
                validaciones=validaciones,
                advertencias=advertencias,
                faltantes=faltantes,
            )

        return self._analisis_alfa_simulado(expediente_id, datos.advertencias)

    def _analisis_alfa_simulado(self, expediente_id: str, advertencias_pdf: list[str]) -> AnalisisOPRead:
        importe_bruto = 3509316.41
        importe_neto = 2920686.82
        cantidad_uc = calcular_uc(importe_bruto)
        procedimiento = determinar_procedimiento(cantidad_uc)

        documentos_comerciales = [
            DocumentoComercialExtraido(
                tipo="Factura",
                letra="B",
                numero="00001-00000394",
                fecha="18/11/2025",
                importe=2206476.02,
            ),
            DocumentoComercialExtraido(
                tipo="Factura",
                letra="B",
                numero="00001-00000395",
                fecha="18/11/2025",
                importe=1302840.39,
            ),
        ]

        retenciones = [
            RetencionExtraida(concepto="Retención Ganancias", importe=14377.81),
            RetencionExtraida(concepto="Retención Ingresos Brutos", importe=58005.23),
            RetencionExtraida(concepto="Retención SUSS Rég. General", importe=29002.62),
            RetencionExtraida(concepto="Retención IVA a Inscriptos", importe=487243.93),
        ]

        validaciones = [
            "OP detectada y asociada al expediente.",
            "Proveedor identificado.",
            "CUIT identificado.",
            "Fondo Compensador identificado.",
            "Documentos comerciales detectados.",
            "Retenciones detectadas.",
            "UC calculadas.",
            "Procedimiento determinado.",
        ]

        advertencias = list(advertencias_pdf)
        advertencias.append("No se pudo extraer texto real suficiente. Se mantiene análisis Alfa simulado.")

        return AnalisisOPRead(
            expediente_id=expediente_id,
            modo="ALFA_SIMULADO",
            op_detectada=True,
            proveedor="CONSTRUCTORA 4M SRL",
            cuit="30-71807806-3",
            fondo="Fondo Compensador",
            orden_pago="OP 1/2025",
            liquidacion="2025-101",
            fecha_op="29/11/2025",
            importe_bruto=importe_bruto,
            importe_neto=importe_neto,
            valor_uc=VALOR_UC_VIGENTE,
            norma_uc=NORMA_UC,
            cantidad_uc=cantidad_uc,
            procedimiento=procedimiento,
            encuadre_legal=encuadre_legal(procedimiento),
            documentos_comerciales=documentos_comerciales,
            retenciones=retenciones,
            validaciones=validaciones,
            advertencias=advertencias,
            faltantes=[
                "Remito o conformidad firmada",
                "Validación CAE",
                "Certificado Fiscal ARBA",
                "Constancia ARCA",
            ],
        )


analisis_op_service = AnalisisOPService()
