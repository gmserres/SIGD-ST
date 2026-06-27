from datetime import datetime

from app.schemas.documento import DocumentoCreate, DocumentoRead


class DocumentoService:
    def __init__(self) -> None:
        self._documentos: dict[str, list[DocumentoRead]] = {}

    def agregar(self, expediente_id: str, data: DocumentoCreate) -> DocumentoRead:
        documento_id = f"DOC-{sum(len(v) for v in self._documentos.values()) + 1:06d}"
        documento = DocumentoRead(
            id=documento_id,
            expediente_id=expediente_id,
            tipo=data.tipo,
            nombre_archivo=data.nombre_archivo,
            ruta=data.ruta,
            fecha_carga=datetime.now(),
            observaciones=data.observaciones,
            tamano_bytes=data.tamano_bytes,
            mime_type=data.mime_type,
        )
        self._documentos.setdefault(expediente_id, []).append(documento)
        return documento

    def listar_por_expediente(self, expediente_id: str) -> list[DocumentoRead]:
        return self._documentos.get(expediente_id, [])

    def obtener(self, expediente_id: str, documento_id: str) -> DocumentoRead | None:
        return next((doc for doc in self.listar_por_expediente(expediente_id) if doc.id == documento_id), None)


documento_service = DocumentoService()
