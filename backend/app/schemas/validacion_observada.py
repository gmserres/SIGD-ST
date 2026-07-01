from pydantic import BaseModel, Field


class ValidacionObservadaCreate(BaseModel):
    motivo: str = Field(..., min_length=10, examples=["Se continúa con observaciones porque la documentación será incorporada en etapa posterior."])
    usuario: str = Field(default="Secretario Técnico")
