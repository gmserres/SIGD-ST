from dataclasses import dataclass
from datetime import date


@dataclass
class DecisionAdministrativa:
    id_decision: str
    solicitud_intervencion_id: str
    autoridad_decisora: str
    fecha_decision: date
    resultado: str
    fundamento: str
    fondo_interviniente: str | None
    descripcion_fondo: str | None
    usuario_registrante: str

    @property
    def aprueba_intervencion(self) -> bool:
        return self.resultado == "Aprobar intervención"
