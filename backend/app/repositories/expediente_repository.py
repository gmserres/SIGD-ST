from typing import Protocol

from app.domain.expediente import Expediente


class ExpedienteRepository(Protocol):
    def siguiente_id(self) -> str:
        ...

    def guardar(self, expediente: Expediente) -> None:
        ...

    def obtener_por_id(self, expediente_id: str) -> Expediente | None:
        ...

    def listar(self) -> list[Expediente]:
        ...
