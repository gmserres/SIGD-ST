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
                modo="ALFA_SIMULADO",
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

        suma_facturas = round(sum(doc.importe for doc in documentos_comerciales), 2)
        total_retenciones = round(sum(ret.importe for ret in retenciones), 2)

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

        advertencias = []
        faltantes = [
            "Remito o conformidad firmada",
            "Validación CAE",
            "Certificado Fiscal ARBA",
            "Constancia ARCA",
        ]

        if suma_facturas != importe_bruto:
            advertencias.append("La suma de documentos comerciales no coincide con el monto total de facturas.")

        if round(importe_bruto - total_retenciones, 2) != importe_neto:
            advertencias.append("El monto neto no coincide con bruto menos retenciones.")

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
            faltantes=faltantes,
        )


analisis_op_service = AnalisisOPService()
