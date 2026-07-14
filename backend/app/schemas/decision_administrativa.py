from datetime import date

from pydantic import BaseModel


class DecisionAdministrativaCreate(BaseModel):
    solicitud_intervencion_id: str
    autoridad_decisora: str
    fecha_decision: date
    resultado: str
    fundamento: str


class DecisionAdministrativaRead(BaseModel):
    id_decision: str
    solicitud_intervencion_id: str
    autoridad_decisora: str
    fecha_decision: date
    resultado: str
    fundamento: str
