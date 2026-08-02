from datetime import date
from typing import Protocol

from app.domain.expediente import Expediente


class ExpedienteNoEncontradoAlRegistrarArchivoError(LookupError):
    pass


class EstadoExpedienteIncompatibleParaArchivoError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"El expediente {expediente_id} no está en estado FIRMADO."
        )


class ArchivoYaRegistradoError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"El expediente {expediente_id} ya posee un archivo registrado "
            "o metadatos de archivo inconsistentes."
        )


class FirmaAusenteOInconsistenteAlArchivarError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"El expediente {expediente_id} no posee una firma completa "
            "y consistente."
        )


class FechaArchivoAnteriorAFirmaError(ValueError):
    def __init__(self, expediente_id: str) -> None:
        super().__init__(
            f"La fecha de archivo del expediente {expediente_id} no puede "
            "ser anterior a la fecha de firma."
        )


class RegistrarArchivoPersistence(Protocol):
    def registrar(
        self,
        expediente_id: str,
        fecha_archivo: date,
        usuario_registro_archivo: str,
    ) -> Expediente:
        ...
