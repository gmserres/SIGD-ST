from datetime import datetime

from app.repositories.documento_repository import (
    DocumentoRepository,
)
from app.repositories.cargar_op_persistence import CargarOPPersistence
from app.schemas.documento import DocumentoCreate, DocumentoRead


class DocumentoService:
    def __init__(
        self,
        repository: DocumentoRepository,
        cargar_op_persistence: CargarOPPersistence | None = None,
    ) -> None:
        self._repository = repository
        self._cargar_op_persistence = cargar_op_persistence

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

    def obtener_por_id(self, documento_id: str) -> DocumentoRead | None:
        return self._repository.obtener_por_id(documento_id)

    def agregar_op(
        self,
        expediente_id: str,
        data: DocumentoCreate,
    ) -> DocumentoRead:
        if self._cargar_op_persistence is None:
            return self.agregar(expediente_id, data)
        return self._cargar_op_persistence.guardar(
            expediente_id,
            data,
            datetime.now(),
        )
