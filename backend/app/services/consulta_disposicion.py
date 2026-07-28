from dataclasses import asdict

from app.repositories.disposicion_repository import (
    DisposicionRepository,
)
from app.schemas.disposicion import DisposicionEmitidaRead


class DisposicionEmitidaNoEncontradaError(LookupError):
    def __init__(self, expediente_id: str) -> None:
        self.expediente_id = expediente_id
        super().__init__(
            f"No existe una Disposición emitida para el "
            f"expediente {expediente_id}."
        )


class ConsultaDisposicionService:
    def __init__(
        self,
        repository: DisposicionRepository,
    ) -> None:
        self._repository = repository

    def obtener_por_expediente(
        self,
        expediente_id: str,
    ) -> DisposicionEmitidaRead:
        disposicion = self._repository.obtener_por_expediente(
            expediente_id
        )
        if disposicion is None:
            raise DisposicionEmitidaNoEncontradaError(expediente_id)
        return DisposicionEmitidaRead(**asdict(disposicion))
