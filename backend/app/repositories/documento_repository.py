from datetime import datetime
from typing import Protocol

from app.schemas.documento import DocumentoCreate, DocumentoRead


class DocumentoRepository(Protocol):
    def guardar(
        self,
        expediente_id: str,
        data: DocumentoCreate,
        fecha_carga: datetime,
    ) -> DocumentoRead:
        ...

    def obtener(
        self,
        expediente_id: str,
        documento_id: str,
    ) -> DocumentoRead | None:
        ...

    def obtener_por_id(
        self,
        documento_id: str,
    ) -> DocumentoRead | None:
        ...

    def listar_por_expediente(
        self,
        expediente_id: str,
    ) -> list[DocumentoRead]:
        ...
