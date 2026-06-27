from pathlib import Path

from app.modules.documentos.extractor_pdf import extraer_texto_pdf
from app.schemas.texto_documento import TextoDocumentoRead
from app.services.documentos import documento_service


class TextoDocumentoService:
    def extraer(self, expediente_id: str, documento_id: str) -> TextoDocumentoRead:
        documento = documento_service.obtener(expediente_id, documento_id)

        if documento is None:
            return TextoDocumentoRead(
                expediente_id=expediente_id,
                documento_id=documento_id,
                nombre_archivo="",
                paginas=0,
                caracteres=0,
                texto="",
                advertencias=["Documento no encontrado."],
            )

        ruta = Path(__file__).resolve().parents[3] / documento.ruta
        texto, paginas, advertencias = extraer_texto_pdf(ruta)

        return TextoDocumentoRead(
            expediente_id=expediente_id,
            documento_id=documento_id,
            nombre_archivo=documento.nombre_archivo,
            paginas=paginas,
            caracteres=len(texto),
            texto=texto[:8000],
            advertencias=advertencias,
        )


texto_documento_service = TextoDocumentoService()
