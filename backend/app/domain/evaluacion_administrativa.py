from dataclasses import dataclass
from datetime import date


@dataclass
class EvaluacionAdministrativa:
    id_evaluacion: str
    solicitud_intervencion_id: str
    fecha_inicio: date
    evaluador: str
    observaciones: str
