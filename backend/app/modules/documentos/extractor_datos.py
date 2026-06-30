import re
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class FacturaExtraida:
    tipo: str
    letra: str
    numero: str
    fecha: str
    importe: float


@dataclass
class RetencionExtraidaDato:
    concepto: str
    importe: float


@dataclass
class DatosOPExtraidos:
    texto_extraido: str
    paginas: int
    cuit: str | None
    fecha: str | None
    orden_pago: str | None
    liquidacion: str | None
    proveedor: str | None
    fondo: str | None
    monto_total_facturas: float | None
    monto_neto_pagar: float | None
    importe_pago: float | None
    importe_probable: float | None
    importe_contexto: str | None
    facturas: list[FacturaExtraida]
    retenciones: list[RetencionExtraidaDato]
    advertencias: list[str]


def extraer_texto_pdf(ruta: Path) -> tuple[str, int, list[str]]:
    advertencias: list[str] = []

    if not ruta.exists():
        return "", 0, ["Archivo físico no encontrado."]

    if ruta.suffix.lower() != ".pdf":
        return "", 0, ["El documento no es PDF."]

    partes: list[str] = []

    try:
        with fitz.open(ruta) as doc:
            paginas = doc.page_count
            for i, pagina in enumerate(doc, start=1):
                texto = pagina.get_text("text").strip()
                if not texto:
                    advertencias.append(f"Página {i} sin texto extraíble.")
                partes.append(texto)
    except Exception as exc:
        return "", 0, [f"No se pudo leer el PDF: {exc}"]

    texto_total = "\n".join(p for p in partes if p)

    if not texto_total:
        advertencias.append("No se extrajo texto. Puede tratarse de un PDF escaneado.")

    return texto_total, paginas, advertencias


def normalizar_importe(valor: str) -> float | None:
    limpio = valor.replace("$", "").replace(" ", "").strip()

    if "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    else:
        limpio = limpio.replace(",", "")

    try:
        numero = round(float(limpio), 2)
    except ValueError:
        return None

    if numero <= 0 or numero > 1_000_000_000:
        return None

    return numero


def extraer_importe_por_etiqueta(texto: str, etiquetas: list[str]) -> tuple[float | None, str | None]:
    for etiqueta in etiquetas:
        patron = rf"{etiqueta}\s*[:.\- ]*(?:\.|\s)*\$?\s*([0-9]{{1,3}}(?:[.\s][0-9]{{3}})*(?:,[0-9]{{2}})|[0-9]+(?:\.[0-9]{{2}})?)"
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            valor = normalizar_importe(match.group(1))
            if valor is not None:
                return valor, etiqueta
    return None, None


def extraer_cuit(texto: str) -> str | None:
    patron = re.search(r"\b(20|23|24|27|30|33|34)[- ]?\d{8}[- ]?\d\b", texto)
    if not patron:
        return None

    solo_digitos = re.sub(r"\D", "", patron.group(0))
    if len(solo_digitos) != 11:
        return patron.group(0)

    return f"{solo_digitos[:2]}-{solo_digitos[2:10]}-{solo_digitos[10]}"


def extraer_fecha(texto: str) -> str | None:
    match = re.search(r"Fecha\s+Emisi[oó]n\s*[:.\- ]*(?:\.|\s)*(\d{1,2}/\d{1,2}/\d{4})", texto, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    patron = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", texto)
    return patron.group(1) if patron else None


def extraer_orden_pago(texto: str) -> str | None:
    patrones = [
        r"Orden\s+de\s+Pago\s+Nro\.?\s*[:.\- ]*(?:\.|\s)*(OP\s*[A-Z0-9/\-.]+)",
        r"(?:orden\s+de\s+pago|op)\s*(?:n[°ºro.]*|nro\.?|numero)?\s*[:\-]?\s*(OP\s*[A-Z0-9/\-.]+)",
        r"\bOP\s*[:\-]?\s*([A-Z0-9/\-.]+)",
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            valor = match.group(1).strip()
            if not valor.upper().startswith("OP"):
                valor = f"OP {valor}"
            return re.sub(r"\s+", " ", valor)

    return None


def extraer_liquidacion(texto: str) -> str | None:
    match = re.search(r"Liquidaci[oó]n\s+de\s+Pago\s+Nro\.?\s*[:.\- ]*(\d{4}-\d+)", texto, flags=re.IGNORECASE)
    return match.group(1) if match else None


def extraer_fondo(texto: str) -> str | None:
    match = re.search(r"Fondo\s*[:.\- ]*(.+)", texto, flags=re.IGNORECASE)
    if not match:
        return None

    valor = re.sub(r"\s+", " ", match.group(1)).strip()
    return valor[:80] if valor else None


def limpiar_linea(linea: str) -> str:
    return re.sub(r"\s+", " ", linea).strip(" :-\t")


def extraer_proveedor(texto: str, cuit: str | None) -> str | None:
    lineas = [limpiar_linea(l) for l in texto.splitlines() if limpiar_linea(l)]

    patrones = [
        r"Raz[oó]n\s+Social\s*[:.\- ]*(.+)",
        r"(?:proveedor|beneficiario|contratista)\s*[:.\-]\s*(.+)",
        r"(?:señor(?:es)?|sr\.?|sres\.?)\s*[:\-]\s*(.+)",
    ]

    for linea in lineas:
        for patron in patrones:
            match = re.search(patron, linea, flags=re.IGNORECASE)
            if match:
                candidato = limpiar_linea(match.group(1))
                if candidato and len(candidato) > 3:
                    return candidato[:120]

    if cuit:
        cuit_sin_guiones = re.sub(r"\D", "", cuit)
        for idx, linea in enumerate(lineas):
            if cuit in linea or cuit_sin_guiones in re.sub(r"\D", "", linea):
                for siguiente in lineas[idx + 1:idx + 5]:
                    if len(siguiente) > 4 and not re.search(r"iva|fondo|rubro|cuit|cuil", siguiente, re.I):
                        return siguiente[:120]
                for anterior in reversed(lineas[max(0, idx - 4):idx]):
                    if len(anterior) > 4 and not re.search(r"cuit|cuil|fecha|expediente|orden", anterior, re.I):
                        return anterior[:120]

    return None


def extraer_retenciones(texto: str) -> list[RetencionExtraidaDato]:
    retenciones: list[RetencionExtraidaDato] = []
    patrones = [
        (r"Retenci[oó]n\s+Ganancias\s*[:.\- ]*(?:\.|\s)*\$?\s*([0-9.]+,[0-9]{2})", "Retención Ganancias"),
        (r"Retenci[oó]n\s+Ingresos\s+Brutos\s*[:.\- ]*(?:\.|\s)*\$?\s*([0-9.]+,[0-9]{2})", "Retención Ingresos Brutos"),
        (r"Retenci[oó]n\s+Iva\s+a\s+Inscriptos\s*[:.\- ]*(?:\.|\s)*\$?\s*([0-9.]+,[0-9]{2})", "Retención IVA a Inscriptos"),
        (r"Retenci[oó]n\s+IVA\s*[:.\- ]*(?:\.|\s)*\$?\s*([0-9.]+,[0-9]{2})", "Retención IVA"),
        (r"Retenci[oó]n\s+SUSS.*?[:.\- ]*(?:\.|\s)*\$?\s*([0-9.]+,[0-9]{2})", "Retención SUSS"),
    ]

    for patron, concepto in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            importe = normalizar_importe(match.group(1))
            if importe is not None:
                retenciones.append(RetencionExtraidaDato(concepto=concepto, importe=importe))

    return retenciones


def extraer_facturas_liquidadas(texto: str) -> list[FacturaExtraida]:
    facturas: list[FacturaExtraida] = []

    patron = re.compile(
        r"(FAC\[[A-Z]\]\d{5}-\d{8})\s+(\d{1,2}/\d{1,2}/\d{4})\s+\$?\s*([0-9.]+,[0-9]{2})",
        flags=re.IGNORECASE,
    )

    for match in patron.finditer(texto):
        codigo = match.group(1)
        fecha = match.group(2)
        importe = normalizar_importe(match.group(3))
        if importe is None:
            continue

        letra_match = re.search(r"FAC\[([A-Z])\]", codigo, flags=re.IGNORECASE)
        numero_match = re.search(r"\](\d{5}-\d{8})", codigo)

        facturas.append(
            FacturaExtraida(
                tipo="Factura",
                letra=letra_match.group(1).upper() if letra_match else "",
                numero=numero_match.group(1) if numero_match else codigo,
                fecha=fecha,
                importe=importe,
            )
        )

    return facturas


def extraer_datos_op_desde_pdf(ruta: Path) -> DatosOPExtraidos:
    texto, paginas, advertencias = extraer_texto_pdf(ruta)

    if not texto:
        return DatosOPExtraidos(
            texto_extraido="",
            paginas=paginas,
            cuit=None,
            fecha=None,
            orden_pago=None,
            liquidacion=None,
            proveedor=None,
            fondo=None,
            monto_total_facturas=None,
            monto_neto_pagar=None,
            importe_pago=None,
            importe_probable=None,
            importe_contexto=None,
            facturas=[],
            retenciones=[],
            advertencias=advertencias,
        )

    cuit = extraer_cuit(texto)
    monto_total, contexto_total = extraer_importe_por_etiqueta(texto, ["Monto Total de Facturas", "Monto Total"])
    monto_neto, contexto_neto = extraer_importe_por_etiqueta(texto, ["Monto Neto a Pagar", "Neto a Pagar"])
    importe_pago, contexto_pago = extraer_importe_por_etiqueta(texto, ["Importe"])

    importe_probable = monto_total or importe_pago or monto_neto
    contexto = contexto_total or contexto_pago or contexto_neto

    return DatosOPExtraidos(
        texto_extraido=texto,
        paginas=paginas,
        cuit=cuit,
        fecha=extraer_fecha(texto),
        orden_pago=extraer_orden_pago(texto),
        liquidacion=extraer_liquidacion(texto),
        proveedor=extraer_proveedor(texto, cuit),
        fondo=extraer_fondo(texto),
        monto_total_facturas=monto_total,
        monto_neto_pagar=monto_neto,
        importe_pago=importe_pago,
        importe_probable=importe_probable,
        importe_contexto=contexto,
        facturas=extraer_facturas_liquidadas(texto),
        retenciones=extraer_retenciones(texto),
        advertencias=advertencias,
    )
