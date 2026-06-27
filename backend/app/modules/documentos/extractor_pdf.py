from pathlib import Path

import fitz


def extraer_texto_pdf(ruta: Path) -> tuple[str, int, list[str]]:
    advertencias: list[str] = []

    if not ruta.exists():
        return "", 0, ["Archivo físico no encontrado."]

    if ruta.suffix.lower() != ".pdf":
        return "", 0, ["El documento no es PDF."]

    texto_partes: list[str] = []

    try:
        with fitz.open(ruta) as doc:
            paginas = doc.page_count
            for indice, pagina in enumerate(doc, start=1):
                texto = pagina.get_text("text").strip()
                if not texto:
                    advertencias.append(f"Página {indice} sin texto extraíble.")
                texto_partes.append(texto)
    except Exception as exc:
        return "", 0, [f"No se pudo leer el PDF: {exc}"]

    texto_total = "\n\n".join(parte for parte in texto_partes if parte)

    if not texto_total:
        advertencias.append("No se extrajo texto. Puede tratarse de un PDF escaneado.")

    return texto_total, paginas, advertencias
