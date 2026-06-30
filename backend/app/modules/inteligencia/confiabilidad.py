def calcular_confiabilidad(
    *,
    op_detectada: bool,
    proveedor: str | None,
    cuit: str | None,
    importe_bruto: float | None,
    importe_neto: float | None,
    facturas_detectadas: int,
    economia_consistente: bool,
    retenciones_detectadas: int,
    faltantes: list[str],
) -> int:
    puntaje = 0

    if op_detectada:
        puntaje += 15
    if proveedor:
        puntaje += 10
    if cuit:
        puntaje += 10
    if importe_bruto:
        puntaje += 10
    if importe_neto:
        puntaje += 10
    if facturas_detectadas > 0:
        puntaje += 15
    if economia_consistente:
        puntaje += 20
    if retenciones_detectadas > 0:
        puntaje += 5

    penalizacion = min(len(faltantes) * 3, 15)
    puntaje = max(0, puntaje - penalizacion)

    return min(100, puntaje)


def calcular_prioridad(*, confiabilidad: int, economia_consistente: bool, faltantes: list[str]) -> str:
    if not economia_consistente or confiabilidad < 45:
        return "ALTA"

    if len(faltantes) >= 3 or confiabilidad < 80:
        return "MEDIA"

    return "BAJA"
