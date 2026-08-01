from dataclasses import asdict
from datetime import date
from typing import Callable

from app.repositories.registrar_firma_persistence import (
    RegistrarFirmaPersistence,
)
from app.schemas.expediente import ExpedienteRead


USUARIO_REGISTRO_FIRMA = "Secretario Técnico"


class FechaFirmaFuturaError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"La fecha de firma del expediente {expediente_id} no puede "
            "ser futura."
        )


class RegistroFirmaService:
    def __init__(
        self,
        persistence: RegistrarFirmaPersistence,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._persistence = persistence
        self._today = today

    def registrar(
        self,
        expediente_id: str,
        fecha_firma: date,
    ) -> ExpedienteRead:
        if fecha_firma > self._today():
            raise FechaFirmaFuturaError(expediente_id)
        actualizado = self._persistence.registrar(
            expediente_id,
            fecha_firma,
            USUARIO_REGISTRO_FIRMA,
        )
        return ExpedienteRead(**asdict(actualizado))
