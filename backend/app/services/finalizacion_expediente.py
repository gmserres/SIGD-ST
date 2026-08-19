from dataclasses import asdict
from datetime import datetime
from typing import Callable

from app.repositories.finalizacion_expediente_persistence import (
    FinalizacionExpedientePersistence,
)
from app.schemas.expediente import ExpedienteRead
from app.schemas.finalizacion_expediente import (
    CierreExpedienteCreate,
    DesistimientoExpedienteCreate,
    HabilitacionCierreRead,
    HabilitacionDesistimientoRead,
)


USUARIO_FINALIZACION = "sistema"


class FechaFinalizacionFuturaError(ValueError):
    pass


class FinalizacionExpedienteService:
    def __init__(
        self,
        persistence: FinalizacionExpedientePersistence,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._persistence = persistence
        self._now = now

    def habilitacion_cierre(self, expediente_id: str) -> HabilitacionCierreRead:
        return self._persistence.habilitacion_cierre(expediente_id)

    def habilitacion_desistimiento(
        self, expediente_id: str
    ) -> HabilitacionDesistimientoRead:
        return self._persistence.habilitacion_desistimiento(expediente_id)

    def cerrar(self, expediente_id: str, data: CierreExpedienteCreate) -> ExpedienteRead:
        ahora = self._now()
        if data.fecha_cierre > ahora.date():
            raise FechaFinalizacionFuturaError("La fecha de cierre no puede ser futura.")
        resultado = self._persistence.cerrar(
            expediente_id, data.fecha_cierre, USUARIO_FINALIZACION, ahora
        )
        return ExpedienteRead(**asdict(resultado))

    def desistir(
        self, expediente_id: str, data: DesistimientoExpedienteCreate
    ) -> ExpedienteRead:
        ahora = self._now()
        if data.fecha_desistimiento > ahora.date():
            raise FechaFinalizacionFuturaError(
                "La fecha de desistimiento no puede ser futura."
            )
        resultado = self._persistence.desistir(
            expediente_id,
            data.fecha_desistimiento,
            data.motivo_desistimiento,
            USUARIO_FINALIZACION,
            ahora,
        )
        return ExpedienteRead(**asdict(resultado))
