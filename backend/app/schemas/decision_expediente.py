from pydantic import BaseModel


class CrearExpedienteDesdeDecision(BaseModel):
    numero_interno: str
    numero_gdeba: str | None = None
    tipo_tramite: str = "FONDO_COMPENSADOR"
