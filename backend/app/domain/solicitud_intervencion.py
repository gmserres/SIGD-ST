from dataclasses import dataclass
from datetime import date


@dataclass
class SolicitudIntervencion:
    id_solicitud: str
    numero_solicitud: str
    procedencia: str
    id_suna: str | None
    fecha_ingreso: date
    establecimiento: str
    solicitante: str
    motivo: str
    prioridad: str
    # Los valores del ciclo de vida permanecen pendientes de definición funcional
    # y no deben asumirse durante la implementación.
    estado: str
