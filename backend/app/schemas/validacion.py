from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator


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


class ControlValidacionSnapshotRead(BaseModel):
    orden: int
    codigo: str
    estado: str
    observacion: str | None = None


class ValidacionAdministrativaRead(BaseModel):
    id: int | None = None
    expediente_id: str
    resultado: Literal[
        "VALIDADA",
        "VALIDADA_CON_OBSERVACIONES",
    ]
    usuario: str
    fecha_validacion: datetime
    motivo_observacion: str | None = None
    estado_expediente: str
    controles: list[ControlValidacionSnapshotRead]
    fecha_invalidacion: datetime | None = None
    motivo_invalidacion: str | None = None
    usuario_invalidacion: str | None = None

    @model_validator(mode="after")
    def validar_motivo(self) -> "ValidacionAdministrativaRead":
        motivo = (
            self.motivo_observacion.strip()
            if self.motivo_observacion is not None
            else None
        )
        if self.resultado == "VALIDADA":
            self.motivo_observacion = None
        elif not motivo:
            raise ValueError(
                "La validación con observaciones exige un motivo."
            )
        else:
            self.motivo_observacion = motivo

        metadatos_invalidacion = (
            self.fecha_invalidacion,
            self.motivo_invalidacion,
            self.usuario_invalidacion,
        )
        if any(valor is not None for valor in metadatos_invalidacion):
            if not all(
                valor is not None for valor in metadatos_invalidacion
            ):
                raise ValueError(
                    "Los metadatos de invalidación deben estar "
                    "completos."
                )
        return self
