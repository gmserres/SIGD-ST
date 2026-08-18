from dataclasses import asdict

from app.repositories.disposicion_repository import DisposicionRepository
from app.schemas.disposicion import DisposicionEmitidaRead


class DisposicionEmitidaNoEncontradaError(LookupError):
    def __init__(
        self,
        expediente_id: str,
        documento_op_id: str | None = None,
    ) -> None:
        self.expediente_id = expediente_id
        self.documento_op_id = documento_op_id
        destino = (
            f"la OP {documento_op_id} del expediente {expediente_id}"
            if documento_op_id is not None
            else f"el expediente {expediente_id}"
        )
        super().__init__(f"No existe una Disposición emitida para {destino}.")


class ConsultaDisposicionService:
    def __init__(self, repository: DisposicionRepository) -> None:
        self._repository = repository

    def obtener_por_expediente(
        self, expediente_id: str
    ) -> DisposicionEmitidaRead:
        disposicion = self._repository.obtener_por_expediente(expediente_id)
        if disposicion is None:
            raise DisposicionEmitidaNoEncontradaError(expediente_id)
        return DisposicionEmitidaRead(**asdict(disposicion))

    def obtener_por_documento_op(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> DisposicionEmitidaRead:
        disposicion = self._repository.obtener_por_documento_op(
            documento_op_id
        )
        if disposicion is None or disposicion.expediente_id != expediente_id:
            raise DisposicionEmitidaNoEncontradaError(
                expediente_id, documento_op_id
            )
        return DisposicionEmitidaRead(**asdict(disposicion))
