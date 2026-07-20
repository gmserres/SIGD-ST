from datetime import date

from pydantic import BaseModel, field_validator, model_validator


class SolicitudIntervencionCreate(BaseModel):
    numero_solicitud: str
    procedencia: str
    id_suna: str | None = None
    fecha_ingreso: date
    establecimiento: str
    solicitante: str
    motivo: str
    prioridad: str

    @field_validator("numero_solicitud")
    @classmethod
    def validar_numero_solicitud_obligatorio(
        cls,
        numero_solicitud: str,
    ) -> str:
        if not numero_solicitud.strip():
            raise ValueError("numero_solicitud es obligatorio")
        return numero_solicitud

    @model_validator(mode="after")
    def validar_id_suna_para_procedencia_suna(
        self,
    ) -> "SolicitudIntervencionCreate":
        es_procedencia_suna = self.procedencia.strip().upper() == "SUNA"
        id_suna_ausente = self.id_suna is None or not self.id_suna.strip()

        if es_procedencia_suna and id_suna_ausente:
            raise ValueError("id_suna es obligatorio cuando la procedencia es SUNA")
        return self


class SolicitudIntervencionUpdate(SolicitudIntervencionCreate):
    pass


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
