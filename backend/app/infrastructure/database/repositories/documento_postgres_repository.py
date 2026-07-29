from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.mappers.documento_mapper import (
    a_modelo,
    a_schema,
)
from app.infrastructure.database.models.documento_model import (
    DocumentoModel,
)
from app.schemas.documento import DocumentoCreate, DocumentoRead


class PostgresDocumentoRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(
        self,
        expediente_id: str,
        data: DocumentoCreate,
        fecha_carga: datetime,
    ) -> DocumentoRead:
        with self._session_factory() as session:
            try:
                modelo = a_modelo(
                    expediente_id,
                    data,
                    fecha_carga,
                )
                session.add(modelo)
                session.flush()
                documento = a_schema(modelo)
                session.commit()
                return documento
            except Exception:
                session.rollback()
                raise

    def obtener(
        self,
        expediente_id: str,
        documento_id: str,
    ) -> DocumentoRead | None:
        secuencia = self._obtener_secuencia(documento_id)
        if secuencia is None:
            return None

        with self._session_factory() as session:
            modelo = session.scalar(
                select(DocumentoModel).where(
                    DocumentoModel.secuencia == secuencia,
                    DocumentoModel.expediente_id == expediente_id,
                )
            )
            return a_schema(modelo) if modelo is not None else None

    def listar_por_expediente(
        self,
        expediente_id: str,
    ) -> list[DocumentoRead]:
        with self._session_factory() as session:
            modelos = session.scalars(
                select(DocumentoModel)
                .where(
                    DocumentoModel.expediente_id == expediente_id
                )
                .order_by(
                    DocumentoModel.fecha_carga,
                    DocumentoModel.secuencia,
                )
            ).all()
            return [a_schema(modelo) for modelo in modelos]

    @staticmethod
    def _obtener_secuencia(documento_id: str) -> int | None:
        prefijo = "DOC-"
        if not documento_id.startswith(prefijo):
            return None

        valor = documento_id[len(prefijo):]
        if not valor.isdigit():
            return None

        return int(valor)
