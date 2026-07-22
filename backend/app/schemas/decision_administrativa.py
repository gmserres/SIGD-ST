from datetime import date
from typing import Literal

from pydantic import BaseModel, model_validator


FondoInterviniente = Literal["FONDO_COMPENSADOR", "CUFP", "OTRO"]


class DecisionAdministrativaCreate(BaseModel):
    solicitud_intervencion_id: str
    autoridad_decisora: str
    fecha_decision: date
    resultado: str
    fundamento: str
    fondo_interviniente: FondoInterviniente | None = None
    descripcion_fondo: str | None = None
    usuario_registrante: str

    @model_validator(mode="after")
    def validar_descripcion_otro(
        self,
    ) -> "DecisionAdministrativaCreate":
        if (
            self.fondo_interviniente == "OTRO"
            and not (self.descripcion_fondo or "").strip()
        ):
            raise ValueError(
                "La descripción del Fondo Interviniente es obligatoria "
                "cuando se selecciona OTRO."
            )
        return self


class DecisionAdministrativaRead(BaseModel):
    id_decision: str
    solicitud_intervencion_id: str
    autoridad_decisora: str
    fecha_decision: date
    resultado: str
    fundamento: str
    fondo_interviniente: FondoInterviniente | None
    descripcion_fondo: str | None
    usuario_registrante: str
