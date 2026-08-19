from datetime import date, datetime
from typing import Protocol

from app.domain.expediente import Expediente
from app.schemas.finalizacion_expediente import (
    HabilitacionCierreRead,
    HabilitacionDesistimientoRead,
)


class FinalizacionExpedienteError(ValueError):
    pass


class FechaCierreAnteriorAFormalizacionError(FinalizacionExpedienteError):
    pass


class FechaDesistimientoAnteriorACreacionError(FinalizacionExpedienteError):
    pass


class FinalizacionExpedientePersistence(Protocol):
    def habilitacion_cierre(self, expediente_id: str) -> HabilitacionCierreRead: ...

    def habilitacion_desistimiento(
        self, expediente_id: str
    ) -> HabilitacionDesistimientoRead: ...

    def cerrar(
        self,
        expediente_id: str,
        fecha: date,
        usuario: str,
        registrado_en: datetime,
    ) -> Expediente: ...

    def desistir(
        self,
        expediente_id: str,
        fecha: date,
        motivo: str,
        usuario: str,
        registrado_en: datetime,
    ) -> Expediente: ...
