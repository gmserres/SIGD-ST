from datetime import date, datetime
from typing import Protocol

from app.domain.disposicion import Disposicion


class DisposicionNoEncontradaAlFormalizarError(LookupError):
    pass


class DisposicionYaFormalizadaError(ValueError):
    pass


class ExpedienteDisposicionNoEncontradoError(LookupError):
    pass


class FechaFormalizacionAnteriorAEmisionError(ValueError):
    pass


class FormalizacionDisposicionPersistence(Protocol):
    def formalizar(
        self,
        id_disposicion: str,
        fecha_formalizacion: date,
        usuario_registro: str,
        registrado_en: datetime,
    ) -> Disposicion:
        ...
