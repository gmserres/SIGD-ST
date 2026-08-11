from typing import Protocol

from app.domain.disposicion import Disposicion


class DisposicionYaRegistradaError(ValueError):
    def __init__(self, criterio: str, valor: str) -> None:
        self.criterio = criterio
        self.valor = valor
        super().__init__(
            f"Ya existe una Disposición con {criterio}: {valor}."
        )


class DisposicionExpedienteAmbiguoError(LookupError):
    def __init__(self, expediente_id: str) -> None:
        self.expediente_id = expediente_id
        super().__init__(
            f"El Expediente {expediente_id} posee más de una "
            "Disposición; la consulta debe direccionarse por OP."
        )


class DisposicionRepository(Protocol):
    def guardar(self, disposicion: Disposicion) -> None:
        ...

    def obtener_por_id(
        self, disposicion_id: str
    ) -> Disposicion | None:
        ...

    def obtener_por_expediente(
        self, expediente_id: str
    ) -> Disposicion | None:
        ...

    def obtener_por_numero(
        self, numero_disposicion: str
    ) -> Disposicion | None:
        ...

    def obtener_por_documento_op(
        self, documento_op_id: str
    ) -> Disposicion | None:
        ...

    def listar_por_expediente(
        self, expediente_id: str
    ) -> list[Disposicion]:
        ...
