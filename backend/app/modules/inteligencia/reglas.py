from dataclasses import dataclass


@dataclass
class DiagnosticoAdministrativo:
    riesgo: str
    recomendacion: str
    resumen: str
    accion_sugerida: str


def diagnosticar_expediente(*, proveedor: str | None, cuit: str | None, importe_bruto: float | None, importe_neto: float | None, facturas_detectadas: int, retenciones_detectadas: int, faltantes: list[str], economia_consistente: bool) -> DiagnosticoAdministrativo:
    datos_esenciales_ok = bool(proveedor and cuit and importe_bruto and importe_neto)

    if not datos_esenciales_ok:
        return DiagnosticoAdministrativo(
            riesgo="ALTO",
            recomendacion="Revisar la documentación cargada antes de continuar.",
            resumen="No se detectaron todos los datos esenciales de la Orden de Pago.",
            accion_sugerida="Revisión documental",
        )

    if not economia_consistente:
        return DiagnosticoAdministrativo(
            riesgo="ALTO",
            recomendacion="Enviar a revisión contable por posible inconsistencia de importes.",
            resumen="La información económica no resulta consistente.",
            accion_sugerida="Revisión contable",
        )

    if len(faltantes) >= 3:
        return DiagnosticoAdministrativo(
            riesgo="MEDIO",
            recomendacion="Solicitar o cargar la documentación faltante antes de emitir disposición.",
            resumen="La OP fue interpretada y las facturas resultan consistentes, pero aún falta documentación obligatoria.",
            accion_sugerida="Completar documentación",
        )

    if len(faltantes) > 0:
        return DiagnosticoAdministrativo(
            riesgo="MEDIO",
            recomendacion="Completar los últimos faltantes y continuar con la validación.",
            resumen="El expediente está encaminado, con observaciones documentales menores.",
            accion_sugerida="Validación con observaciones",
        )

    return DiagnosticoAdministrativo(
        riesgo="BAJO",
        recomendacion="El expediente puede avanzar a validación final.",
        resumen="La documentación analizada resulta consistente y no se detectan faltantes críticos.",
        accion_sugerida="Continuar trámite",
    )
