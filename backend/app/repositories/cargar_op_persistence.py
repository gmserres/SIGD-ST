from datetime import datetime
from typing import Protocol

from app.schemas.documento import DocumentoCreate, DocumentoRead


class CargarOPPersistence(Protocol):
    def guardar(
        self,
        expediente_id: str,
        data: DocumentoCreate,
        fecha_carga: datetime,
    ) -> DocumentoRead:
        ...
