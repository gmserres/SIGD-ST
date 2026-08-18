from dataclasses import asdict
from datetime import date, datetime
from typing import Callable

from app.repositories.formalizacion_disposicion_persistence import (
    FormalizacionDisposicionPersistence,
)
from app.schemas.disposicion import DisposicionEmitidaRead


USUARIO_REGISTRO_FORMALIZACION = "sistema"


class FechaFormalizacionFuturaError(ValueError):
    pass


class FormalizacionDisposicionService:
    def __init__(
        self,
        persistence: FormalizacionDisposicionPersistence,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._persistence = persistence
        self._now = now

    def formalizar(
        self,
        id_disposicion: str,
        fecha_formalizacion: date,
    ) -> DisposicionEmitidaRead:
        registrado_en = self._now()
        if fecha_formalizacion > registrado_en.date():
            raise FechaFormalizacionFuturaError(id_disposicion)
        disposicion = self._persistence.formalizar(
            id_disposicion,
            fecha_formalizacion,
            USUARIO_REGISTRO_FORMALIZACION,
            registrado_en,
        )
        return DisposicionEmitidaRead(**asdict(disposicion))
