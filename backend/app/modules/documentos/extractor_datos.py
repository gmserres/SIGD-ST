import re
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class DatosOPExtraidos:
    texto_extraido: str
    paginas: int
    cuit: str | None
    fecha: str | None
    orden_pago: str | None
    proveedor: str | None
    importe_probable: float | None
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
        return round(float(limpio), 2)
    except ValueError:
        return None


def extraer_importes(texto: str) -> list[float]:
    candidatos = re.findall(r"\$?\s*(\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})|\d+(?:\.\d{2})?)", texto)
    importes: list[float] = []

    for candidato in candidatos:
        valor = normalizar_importe(candidato)
        if valor is not None and valor > 0:
            importes.append(valor)

    return importes


def extraer_cuit(texto: str) -> str | None:
    patron = re.search(r"\b(20|23|24|27|30|33|34)[- ]?\d{8}[- ]?\d\b", texto)
    if not patron:
        return None

    solo_digitos = re.sub(r"\D", "", patron.group(0))
    if len(solo_digitos) != 11:
        return patron.group(0)

    return f"{solo_digitos[:2]}-{solo_digitos[2:10]}-{solo_digitos[10]}"


def extraer_fecha(texto: str) -> str | None:
    patron = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", texto)
    return patron.group(1) if patron else None


def extraer_orden_pago(texto: str) -> str | None:
    patrones = [
        r"(?:orden\s+de\s+pago|op)\s*(?:n[°ºro.]*|nro\.?|numero)?\s*[:\-]?\s*([A-Z0-9/\-.]+)",
        r"\bOP\s*[:\-]?\s*([A-Z0-9/\-.]+)",
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def limpiar_linea(linea: str) -> str:
    return re.sub(r"\s+", " ", linea).strip(" :-\t")


def extraer_proveedor(texto: str, cuit: str | None) -> str | None:
    lineas = [limpiar_linea(l) for l in texto.splitlines() if limpiar_linea(l)]

    patrones = [
        r"(?:proveedor|beneficiario|raz[oó]n social|contratista)\s*[:\-]\s*(.+)",
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
            advertencias=advertencias,
        )

    cuit = extraer_cuit(texto)
    importes = extraer_importes(texto)
    importe_probable = max(importes) if importes else None

    return DatosOPExtraidos(
        texto_extraido=texto,
        paginas=paginas,
        cuit=cuit,
        fecha=extraer_fecha(texto),
        orden_pago=extraer_orden_pago(texto),
        proveedor=extraer_proveedor(texto, cuit),
        importe_probable=importe_probable,
        advertencias=advertencias,
    )
