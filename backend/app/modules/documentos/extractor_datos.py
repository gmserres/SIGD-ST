import re
from dataclasses import dataclass
from pathlib import Path

import fitz


IMPORTE_MAXIMO_RAZONABLE = 1_000_000_000


@dataclass
class DatoConConfianza:
    valor: str | float | None
    confianza: int
    contexto: str | None = None


@dataclass
class DatosOPExtraidos:
    texto_extraido: str
    paginas: int
    cuit: str | None
    fecha: str | None
    orden_pago: str | None
    proveedor: str | None
    importe_probable: float | None
    confianza_importe: int
    contexto_importe: str | None
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

    # Formato argentino: 884.000,00
    if "," in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    else:
        limpio = limpio.replace(",", "")

    try:
        numero = round(float(limpio), 2)
    except ValueError:
        return None

    if numero <= 0 or numero > IMPORTE_MAXIMO_RAZONABLE:
        return None

    return numero


def es_identificador_no_importe(linea: str) -> bool:
    texto = linea.lower()
    palabras_bloqueadas = [
        "cbu",
        "cuit",
        "cuil",
        "dni",
        "expediente",
        "liquidación",
        "liquidacion",
        "nro",
        "n°",
        "nº",
        "numero de cbu",
        "número de cbu",
        "orden de pago nro",
    ]
    return any(palabra in texto for palabra in palabras_bloqueadas)


def extraer_importes_genericos(texto: str) -> list[float]:
    candidatos = re.findall(r"\$\s*(\d{1,3}(?:[.]\d{3})*(?:,\d{2})|\d+(?:[.]\d{2})?)", texto)
    importes: list[float] = []

    for candidato in candidatos:
        valor = normalizar_importe(candidato)
        if valor is not None:
            importes.append(valor)

    return importes


def extraer_importe_por_contexto(texto: str) -> tuple[float | None, int, str | None, list[str]]:
    advertencias: list[str] = []
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]

    # Orden de prioridad. Mientras más específica la etiqueta, mayor confianza.
    etiquetas_prioritarias: list[tuple[str, int]] = [
        (r"monto\s+total\s+de\s+facturas", 99),
        (r"monto\s+neto\s+a\s+pagar", 99),
        (r"importe\s+total", 98),
        (r"importe", 97),
        (r"total\s+facturas", 95),
        (r"total", 88),
    ]

    patron_importe = r"\$\s*(\d{1,3}(?:[.]\d{3})*(?:,\d{2})|\d+(?:[.]\d{2})?)"

    for etiqueta, confianza in etiquetas_prioritarias:
        for linea in lineas:
            if not re.search(etiqueta, linea, flags=re.IGNORECASE):
                continue

            if es_identificador_no_importe(linea) and not re.search(r"importe|monto|total", linea, flags=re.IGNORECASE):
                continue

            match = re.search(patron_importe, linea)
            if match:
                valor = normalizar_importe(match.group(1))
                if valor is not None:
                    return valor, confianza, limpiar_linea(linea), advertencias

        # Muchos PDFs extraen la etiqueta y el valor en líneas separadas.
        for indice, linea in enumerate(lineas):
            if not re.search(etiqueta, linea, flags=re.IGNORECASE):
                continue

            if "cbu" in linea.lower():
                continue

            siguientes = lineas[indice: indice + 4]
            bloque = " ".join(siguientes)
            match = re.search(patron_importe, bloque)
            if match:
                valor = normalizar_importe(match.group(1))
                if valor is not None:
                    return valor, confianza - 3, limpiar_linea(bloque), advertencias

    importes = extraer_importes_genericos(texto)
    if importes:
        advertencias.append("No se encontró etiqueta clara de importe; se tomó el mayor valor monetario con símbolo $." )
        return max(importes), 65, "importe monetario genérico", advertencias

    return None, 0, None, advertencias


def extraer_cuit(texto: str) -> str | None:
    patron = re.search(r"\b(20|23|24|27|30|33|34)[- ]?\d{8}[- ]?\d\b", texto)
    if not patron:
        return None

    solo_digitos = re.sub(r"\D", "", patron.group(0))
    if len(solo_digitos) != 11:
        return patron.group(0)

    return f"{solo_digitos[:2]}-{solo_digitos[2:10]}-{solo_digitos[10]}"


def extraer_fecha(texto: str) -> str | None:
    # Prioriza Fecha Emisión si existe.
    match_emision = re.search(r"fecha\s+emisi[oó]n\s*[:.]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", texto, flags=re.IGNORECASE)
    if match_emision:
        return match_emision.group(1)

    patron = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", texto)
    return patron.group(1) if patron else None


def extraer_orden_pago(texto: str) -> str | None:
    patrones = [
        r"orden\s+de\s+pago\s+nro\.?\s*[:.\-]*\s*(OP\s*\d+\s*/\s*\d+)",
        r"orden\s+de\s+pago\s*(?:n[°ºro.]*|nro\.?|numero)?\s*[:.\-]*\s*(OP\s*\d+\s*/\s*\d+)",
        r"\b(OP\s*\d+\s*/\s*\d+)\b",
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip().upper()

    return None


def limpiar_linea(linea: str) -> str:
    return re.sub(r"\s+", " ", linea).strip(" :-\t.")


def extraer_proveedor(texto: str, cuit: str | None) -> str | None:
    lineas = [limpiar_linea(l) for l in texto.splitlines() if limpiar_linea(l)]

    patrones = [
        r"raz[oó]n\s+social\s*[:\-]\s*(.+)",
        r"proveedor\s*[:\-]\s*(.+)",
        r"beneficiario\s*[:\-]\s*(.+)",
        r"contratista\s*[:\-]\s*(.+)",
    ]

    for linea in lineas:
        for patron in patrones:
            match = re.search(patron, linea, flags=re.IGNORECASE)
            if match:
                candidato = limpiar_linea(match.group(1))
                if candidato and len(candidato) > 3:
                    return candidato[:120]

    # Caso típico del PDF: "Razón Social:" en una línea y el nombre en la siguiente.
    # No se usa "Datos del Proveedor" como etiqueta, porque suele estar antes del CUIT.
    for indice, linea in enumerate(lineas):
        if re.search(r"^(raz[oó]n\s+social|beneficiario|contratista|proveedor)\s*:*$", linea, flags=re.IGNORECASE):
            for siguiente in lineas[indice + 1: indice + 5]:
                if re.fullmatch(r"[0-9\- ]+", siguiente):
                    continue
                if len(siguiente) > 3 and not re.search(r"iva|ganancias|suss|fondo|rubro|cuit|cuil", siguiente, re.I):
                    return siguiente[:120]

    if cuit:
        cuit_sin_guiones = re.sub(r"\D", "", cuit)
        for idx, linea in enumerate(lineas):
            if cuit in linea or cuit_sin_guiones in re.sub(r"\D", "", linea):
                for posterior in lineas[idx + 1: idx + 5]:
                    if len(posterior) > 4 and not re.search(r"iva|ganancias|suss|fondo|rubro|cuit", posterior, re.I):
                        return posterior[:120]
                for anterior in reversed(lineas[max(0, idx - 4):idx]):
                    if len(anterior) > 4 and not re.search(r"cuit|cuil|fecha|expediente|orden", anterior, re.I):
                        return anterior[:120]

    return None


def extraer_datos_op_desde_pdf(ruta: Path) -> DatosOPExtraidos:
    texto, paginas, advertencias = extraer_texto_pdf(ruta)

    if not texto:
        return DatosOPExtraidos(
            texto_extraido="",
            paginas=paginas,
            cuit=None,
            fecha=None,
            orden_pago=None,
            proveedor=None,
            importe_probable=None,
            confianza_importe=0,
            contexto_importe=None,
            advertencias=advertencias,
        )

    cuit = extraer_cuit(texto)
    importe, confianza_importe, contexto_importe, advertencias_importe = extraer_importe_por_contexto(texto)
    advertencias.extend(advertencias_importe)

    return DatosOPExtraidos(
        texto_extraido=texto,
        paginas=paginas,
        cuit=cuit,
        fecha=extraer_fecha(texto),
        orden_pago=extraer_orden_pago(texto),
        proveedor=extraer_proveedor(texto, cuit),
        importe_probable=importe,
        confianza_importe=confianza_importe,
        contexto_importe=contexto_importe,
        advertencias=advertencias,
    )
