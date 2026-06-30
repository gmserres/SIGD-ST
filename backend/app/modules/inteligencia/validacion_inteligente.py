from dataclasses import dataclass


@dataclass
class ResultadoValidacionInteligente:
    puede_validar: bool
    errores: list[str]
    advertencias: list[str]
    recomendacion: str


def evaluar_validacion_inteligente(
    *,
    tiene_op: bool,
    proveedor: str | None,
    cuit: str | None,
    importe_bruto: float | None,
    facturas_detectadas: int,
    economia_consistente: bool,
    tipos_documentales: list[str],
) -> ResultadoValidacionInteligente:
    errores: list[str] = []
    advertencias: list[str] = []

    tipos = {t.upper() for t in tipos_documentales}

    if not tiene_op:
        errores.append("Falta Orden de Pago.")
    if not proveedor:
        errores.append("No se detectó proveedor en la OP.")
    if not cuit:
        errores.append("No se detectó CUIT en la OP.")
    if not importe_bruto:
        errores.append("No se detectó importe bruto o monto total.")
    if facturas_detectadas <= 0:
        errores.append("No se detectaron facturas liquidadas en la OP.")
    if not economia_consistente:
        errores.append("La suma de facturas no coincide con el monto total de la OP.")

    # Documentos físicos o tipos documentales cargados.
    if "FACTURA" not in tipos:
        advertencias.append("No se cargó factura como documento complementario.")
    if "REMITO" not in tipos and "CONFORMIDAD" not in tipos and "ACTA_RECEPCION" not in tipos:
        errores.append("Falta remito, conformidad o acta de recepción.")
    if "ARCA" not in tipos:
        errores.append("Falta constancia ARCA.")
    if "ARBA" not in tipos:
        errores.append("Falta certificado fiscal ARBA.")
    if "CAE" not in tipos and "VALIDACION_CAE" not in tipos:
        errores.append("Falta validación CAE.")

    puede_validar = len(errores) == 0

    if puede_validar:
        recomendacion = "El expediente reúne condiciones mínimas para validar."
    else:
        recomendacion = "No se recomienda validar. Deben corregirse los errores críticos."

    return ResultadoValidacionInteligente(
        puede_validar=puede_validar,
        errores=errores,
        advertencias=advertencias,
        recomendacion=recomendacion,
    )
