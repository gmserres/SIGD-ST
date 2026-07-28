from typing import Protocol

from app.domain.disposicion import Disposicion
from app.domain.expediente import Expediente


class ExpedienteNoEncontradoAlEmitirError(LookupError):
    pass


class EstadoExpedienteIncompatibleError(ValueError):
    def __init__(self, expediente_id: str, estado: str) -> None:
        self.expediente_id = expediente_id
        self.estado = estado
        super().__init__(
            f"El expediente {expediente_id} no puede emitir una "
            f"Disposición desde el estado {estado}."
        )


class EmitirDisposicionPersistence(Protocol):
    def emitir(
        self,
        disposicion: Disposicion,
        expediente_id: str,
    ) -> Expediente:
        ...
