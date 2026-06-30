from dataclasses import dataclass


@dataclass
class Evidencia:
    codigo: str
    nombre: str
    estado: str
    fuente: str
    observacion: str


def construir_evidencias(
    *,
    tiene_op: bool,
    proveedor: str | None,
    cuit: str | None,
    facturas_detectadas: int,
    tipos_documentales: list[str],
) -> list[Evidencia]:
    tipos = {t.upper() for t in tipos_documentales}

    def ok(codigo: str, nombre: str, fuente: str, obs: str) -> Evidencia:
        return Evidencia(codigo, nombre, "VERIFICADA", fuente, obs)

    def pendiente(codigo: str, nombre: str, obs: str) -> Evidencia:
        return Evidencia(codigo, nombre, "PENDIENTE", "Sin acreditar", obs)

    evidencias: list[Evidencia] = []

    evidencias.append(
        ok("OP", "Orden de Pago", "PDF", "Orden de Pago cargada.")
        if tiene_op else pendiente("OP", "Orden de Pago", "Falta cargar la Orden de Pago.")
    )

    evidencias.append(
        ok("PROVEEDOR", "Proveedor", "OP", f"Proveedor detectado: {proveedor}.")
        if proveedor else pendiente("PROVEEDOR", "Proveedor", "No se detectó proveedor.")
    )

    evidencias.append(
        ok("CUIT", "CUIT", "OP", f"CUIT detectado: {cuit}.")
        if cuit else pendiente("CUIT", "CUIT", "No se detectó CUIT.")
    )

    facturas_ok = facturas_detectadas > 0 or "FACTURA" in tipos or "CHECK_FACTURA" in tipos
    evidencias.append(
        ok(
            "FACTURAS",
            "Facturas",
            "OP" if facturas_detectadas > 0 else "Archivo/checklist",
            f"{facturas_detectadas} factura(s) liquidadas detectadas en la OP." if facturas_detectadas > 0 else "Facturas acreditadas.",
        )
        if facturas_ok else pendiente("FACTURAS", "Facturas", "Falta acreditar facturas.")
    )

    remito_ok = bool({"REMITO", "CONFORMIDAD", "ACTA_RECEPCION", "CHECK_REMITO"} & tipos)
    evidencias.append(
        ok("REMITO", "Remito / conformidad", "Archivo/checklist", "Remito o conformidad acreditada.")
        if remito_ok else pendiente("REMITO", "Remito / conformidad", "Pendiente de acreditar.")
    )

    cae_ok = bool({"CAE", "VALIDACION_CAE", "CHECK_CAE"} & tipos)
    evidencias.append(
        ok("CAE", "Validación CAE", "Archivo/checklist", "CAE acreditado.")
        if cae_ok else pendiente("CAE", "Validación CAE", "Pendiente de acreditar.")
    )

    arca_ok = bool({"ARCA", "CHECK_ARCA"} & tipos)
    evidencias.append(
        ok("ARCA", "Constancia ARCA", "Archivo/checklist", "Constancia ARCA acreditada.")
        if arca_ok else pendiente("ARCA", "Constancia ARCA", "Pendiente de acreditar.")
    )

    arba_ok = bool({"ARBA", "CHECK_ARBA"} & tipos)
    evidencias.append(
        ok("ARBA", "Certificado ARBA", "Archivo/checklist", "Certificado ARBA acreditado.")
        if arba_ok else pendiente("ARBA", "Certificado ARBA", "Pendiente de acreditar.")
    )

    return evidencias
