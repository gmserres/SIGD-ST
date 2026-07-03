from pydantic import BaseModel, Field


class ParametrosInstitucionalesRead(BaseModel):
    ejercicio: int
    valor_uc: float
    norma_uc: str
    fecha_vigencia_uc: str
    distrito: str
    localidad: str
    organismo: str
    proxima_disposicion: int


class ParametrosInstitucionalesUpdate(BaseModel):
    ejercicio: int | None = None
    valor_uc: float | None = Field(default=None, gt=0)
    norma_uc: str | None = None
    fecha_vigencia_uc: str | None = None
    distrito: str | None = None
    localidad: str | None = None
    organismo: str | None = None
    proxima_disposicion: int | None = Field(default=None, ge=1)
