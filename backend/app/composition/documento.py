from app.composition.expediente import session_factory
from app.infrastructure.database.repositories.documento_postgres_repository import (
    PostgresDocumentoRepository,
)
from app.infrastructure.database.persistence.cargar_op_postgres import (
    PostgresCargarOPPersistence,
)
from app.services.documentos import DocumentoService


documento_repository = PostgresDocumentoRepository(session_factory)
cargar_op_persistence = PostgresCargarOPPersistence(session_factory)
documento_service = DocumentoService(
    documento_repository,
    cargar_op_persistence,
)
