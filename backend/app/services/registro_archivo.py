from dataclasses import asdict
from datetime import date
from typing import Callable

from app.repositories.registrar_archivo_persistence import (
    RegistrarArchivoPersistence,
)
from app.schemas.expediente import ExpedienteRead


USUARIO_REGISTRO_ARCHIVO = "Secretario Técnico"
USUARIO_REGISTRO_ARCHIVO_F6D3 = "sistema"


class FechaArchivoFuturaError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"La fecha de archivo del expediente {expediente_id} no puede "
            "ser futura."
        )


class RegistroArchivoService:
    def __init__(
        self,
        persistence: RegistrarArchivoPersistence,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._persistence = persistence
        self._today = today

    def registrar(
        self,
        expediente_id: str,
        fecha_archivo: date,
    ) -> ExpedienteRead:
        if fecha_archivo > self._today():
            raise FechaArchivoFuturaError(expediente_id)
        actualizado = self._persistence.registrar(
            expediente_id,
            fecha_archivo,
            USUARIO_REGISTRO_ARCHIVO,
        )
        return ExpedienteRead(**asdict(actualizado))

    def registrar_finalizado(
        self,
        expediente_id: str,
        fecha_archivo: date,
    ) -> ExpedienteRead:
        if fecha_archivo > self._today():
            raise FechaArchivoFuturaError(expediente_id)
        actualizado = self._persistence.registrar_finalizado(
            expediente_id,
            fecha_archivo,
            USUARIO_REGISTRO_ARCHIVO_F6D3,
        )
        return ExpedienteRead(**asdict(actualizado))
