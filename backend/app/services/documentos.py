from datetime import datetime

from app.repositories.documento_repository import (
    DocumentoRepository,
)
from app.schemas.documento import DocumentoCreate, DocumentoRead


class DocumentoService:
    def __init__(
        self,
        repository: DocumentoRepository,
    ) -> None:
        self._repository = repository

    def agregar(self, expediente_id: str, data: DocumentoCreate) -> DocumentoRead:
        return self._repository.guardar(
            expediente_id=expediente_id,
            data=data,
            fecha_carga=datetime.now(),
        )

    def listar_por_expediente(self, expediente_id: str) -> list[DocumentoRead]:
        return self._repository.listar_por_expediente(expediente_id)

    def obtener(self, expediente_id: str, documento_id: str) -> DocumentoRead | None:
        return self._repository.obtener(expediente_id, documento_id)
