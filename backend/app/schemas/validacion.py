from pydantic import BaseModel


class ControlValidacion(BaseModel):
    control: str
    estado: str
    observacion: str | None = None


class ValidacionExpedienteRead(BaseModel):
    expediente_id: str
    estado_general: str
    errores: list[str]
    advertencias: list[str]
    controles: list[ControlValidacion]
