from typing import Protocol

from app.domain.expediente import Expediente
from app.schemas.validacion import ValidacionAdministrativaRead


class ExpedienteNoEncontradoAlValidarError(LookupError):
    pass


class ValidarExpedientePersistence(Protocol):
    def validar(
        self,
        validacion: ValidacionAdministrativaRead,
    ) -> tuple[Expediente, ValidacionAdministrativaRead]:
        ...
