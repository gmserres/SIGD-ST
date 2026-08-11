from app.domain.disposicion import Disposicion
from app.repositories.disposicion_repository import (
    DisposicionExpedienteAmbiguoError,
    DisposicionYaRegistradaError,
)


class InMemoryDisposicionRepository:
    def __init__(self) -> None:
        self._por_id: dict[str, Disposicion] = {}

    def guardar(self, disposicion: Disposicion) -> None:
        conflictos = [
            ("id", disposicion.id_disposicion, self.obtener_por_id),
            (
                "numero_disposicion",
                disposicion.numero_disposicion,
                self.obtener_por_numero,
            ),
        ]
        if disposicion.documento_op_id is not None:
            conflictos.append(
                (
                    "documento_op",
                    disposicion.documento_op_id,
                    self.obtener_por_documento_op,
                )
            )
        for criterio, valor, obtener in conflictos:
            if obtener(valor) is not None:
                raise DisposicionYaRegistradaError(criterio, valor)
        self._por_id[disposicion.id_disposicion] = disposicion

    def obtener_por_id(
        self, disposicion_id: str
    ) -> Disposicion | None:
        return self._por_id.get(disposicion_id)

    def obtener_por_expediente(
        self, expediente_id: str
    ) -> Disposicion | None:
        disposiciones = self.listar_por_expediente(expediente_id)
        if len(disposiciones) > 1:
            raise DisposicionExpedienteAmbiguoError(expediente_id)
        return disposiciones[0] if disposiciones else None

    def listar_por_expediente(
        self, expediente_id: str
    ) -> list[Disposicion]:
        return sorted(
            (
                item
                for item in self._por_id.values()
                if item.expediente_id == expediente_id
            ),
            key=lambda item: (
                item.fecha_emision,
                item.id_disposicion,
            ),
        )

    def obtener_por_documento_op(
        self, documento_op_id: str
    ) -> Disposicion | None:
        return next(
            (
                item
                for item in self._por_id.values()
                if item.documento_op_id == documento_op_id
            ),
            None,
        )

    def obtener_por_numero(
        self, numero_disposicion: str
    ) -> Disposicion | None:
        return next(
            (
                item
                for item in self._por_id.values()
                if item.numero_disposicion == numero_disposicion
            ),
            None,
        )
