from datetime import date

from pydantic import BaseModel, model_validator


class SolicitudIntervencionCreate(BaseModel):
    numero_solicitud: str
    procedencia: str
    id_suna: str | None = None
    fecha_ingreso: date
    establecimiento: str
    solicitante: str
    motivo: str
    prioridad: str

    @model_validator(mode="after")
    def validar_id_suna_para_procedencia_suna(
        self,
    ) -> "SolicitudIntervencionCreate":
        es_procedencia_suna = self.procedencia.strip().upper() == "SUNA"
        id_suna_ausente = self.id_suna is None or not self.id_suna.strip()

        if es_procedencia_suna and id_suna_ausente:
            raise ValueError("id_suna es obligatorio cuando la procedencia es SUNA")
        return self


class SolicitudIntervencionRead(BaseModel):
    id_solicitud: str
    numero_solicitud: str
    procedencia: str
    id_suna: str | None
    fecha_ingreso: date
    establecimiento: str
    solicitante: str
    motivo: str
    prioridad: str
    estado: str
