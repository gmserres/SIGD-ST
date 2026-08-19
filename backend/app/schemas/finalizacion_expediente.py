from datetime import date

from pydantic import BaseModel, field_validator

from app.domain.finalizacion_expediente import (
    EstadoHabilitacionCierre,
    EstadoHabilitacionDesistimiento,
)


class OPPendienteCierreRead(BaseModel):
    documento_op_id: str
    nombre_archivo: str
    causa: str


class HabilitacionCierreRead(BaseModel):
    estado: EstadoHabilitacionCierre
    habilitado: bool
    cantidad_op: int
    disposiciones_emitidas: int
    disposiciones_formalizadas: int
    op_pendientes: list[OPPendienteCierreRead]
    mensaje: str
    proxima_accion: str


class HabilitacionDesistimientoRead(BaseModel):
    estado: EstadoHabilitacionDesistimiento
    habilitado: bool
    cantidad_op: int
    mensaje: str
    proxima_accion: str


class CierreExpedienteCreate(BaseModel):
    fecha_cierre: date
    confirmacion_completitud: bool

    @field_validator("confirmacion_completitud")
    @classmethod
    def confirmar_literalmente(cls, valor: bool) -> bool:
        if valor is not True:
            raise ValueError("La confirmación de completitud debe ser verdadera.")
        return valor


class DesistimientoExpedienteCreate(BaseModel):
    fecha_desistimiento: date
    motivo_desistimiento: str

    @field_validator("motivo_desistimiento")
    @classmethod
    def motivo_obligatorio(cls, valor: str) -> str:
        normalizado = valor.strip()
        if not normalizado:
            raise ValueError("El motivo de desistimiento es obligatorio.")
        return normalizado
