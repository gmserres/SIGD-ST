from app.composition.expediente import session_factory
from app.infrastructure.database.repositories.documento_postgres_repository import (
    PostgresDocumentoRepository,
)
from app.services.documentos import DocumentoService


documento_repository = PostgresDocumentoRepository(session_factory)
documento_service = DocumentoService(documento_repository)
