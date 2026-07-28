from app.core.settings import get_database_url
from app.infrastructure.database.repositories.decision_administrativa_postgres_repository import (
    PostgresDecisionAdministrativaRepository,
)
from app.infrastructure.database.session import (
    crear_fabrica_sesiones,
    crear_motor,
)
from app.repositories.decision_administrativa_in_memory_repository import (
    InMemoryDecisionAdministrativaRepository,
)
from app.repositories.decision_administrativa_repository import (
    DecisionAdministrativaRepository,
)
from app.services.decision_administrativa_service import (
    DecisionAdministrativaService,
)


_database_url = get_database_url()

decision_administrativa_repository: DecisionAdministrativaRepository
if _database_url:
    _engine = crear_motor(_database_url)
    _session_factory = crear_fabrica_sesiones(_engine)
    decision_administrativa_repository = (
        PostgresDecisionAdministrativaRepository(_session_factory)
    )
else:
    decision_administrativa_repository = (
        InMemoryDecisionAdministrativaRepository()
    )

decision_administrativa_service = DecisionAdministrativaService(
    decision_administrativa_repository,
)
