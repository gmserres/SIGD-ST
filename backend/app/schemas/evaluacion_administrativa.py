from datetime import date

from pydantic import BaseModel


class EvaluacionAdministrativaCreate(BaseModel):
    solicitud_intervencion_id: str
    fecha_inicio: date
    evaluador: str
    observaciones: str


class EvaluacionAdministrativaRead(BaseModel):
    id_evaluacion: str
    solicitud_intervencion_id: str
    fecha_inicio: date
    evaluador: str
    observaciones: str
