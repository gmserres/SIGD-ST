from datetime import datetime
from typing import Protocol

from app.schemas.validacion import ValidacionAdministrativaRead


class ValidacionAdministrativaRepository(Protocol):
    def registrar(
        self,
        validacion: ValidacionAdministrativaRead,
    ) -> ValidacionAdministrativaRead:
        ...

    def obtener_ultima_por_expediente(
        self,
        expediente_id: str,
    ) -> ValidacionAdministrativaRead | None:
        ...

    def obtener_vigente(
        self,
        expediente_id: str,
    ) -> ValidacionAdministrativaRead | None:
        ...

    def invalidar_vigente(
        self,
        expediente_id: str,
        motivo: str,
        usuario: str,
        fecha: datetime,
    ) -> ValidacionAdministrativaRead | None:
        ...

    def listar_por_expediente(
        self,
        expediente_id: str,
    ) -> list[ValidacionAdministrativaRead]:
        ...
