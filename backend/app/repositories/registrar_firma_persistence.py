from datetime import date
from typing import Protocol

from app.domain.expediente import Expediente


class ExpedienteNoEncontradoAlRegistrarFirmaError(LookupError):
    pass


class EstadoExpedienteIncompatibleParaFirmaError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"El expediente {expediente_id} no está en estado "
            "DISPOSICION_EMITIDA."
        )


class FirmaYaRegistradaError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"El expediente {expediente_id} ya posee una firma registrada."
        )


class DisposicionEmitidaNoEncontradaAlFirmarError(LookupError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"El expediente {expediente_id} no posee una Disposición "
            "emitida persistida."
        )


class FechaFirmaAnteriorAEmisionError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"La fecha de firma del expediente {expediente_id} no puede "
            "ser anterior a la fecha de emisión."
        )


class RegistrarFirmaPersistence(Protocol):
    def registrar(
        self,
        expediente_id: str,
        fecha_firma: date,
        usuario_registro_firma: str,
    ) -> Expediente:
        ...
