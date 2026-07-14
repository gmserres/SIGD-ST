from dataclasses import asdict
from uuid import uuid4

from app.domain.solicitud_intervencion import SolicitudIntervencion
from app.schemas.solicitud_intervencion import (
    SolicitudIntervencionCreate,
    SolicitudIntervencionRead,
)


class SolicitudIntervencionService:
    def __init__(self) -> None:
        self._solicitudes: dict[str, SolicitudIntervencion] = {}

    def crear(
        self,
        data: SolicitudIntervencionCreate,
    ) -> SolicitudIntervencionRead:
        solicitud_id = str(uuid4())
        solicitud = SolicitudIntervencion(
            id_solicitud=solicitud_id,
            numero_solicitud=data.numero_solicitud,
            procedencia=data.procedencia,
            id_suna=data.id_suna,
            fecha_ingreso=data.fecha_ingreso,
            establecimiento=data.establecimiento,
            solicitante=data.solicitante,
            motivo=data.motivo,
            prioridad=data.prioridad,
            estado="REGISTRADA",
        )
        self._solicitudes[solicitud_id] = solicitud
        return SolicitudIntervencionRead(**asdict(solicitud))

    def obtener_por_id(
        self,
        solicitud_id: str,
    ) -> SolicitudIntervencionRead:
        solicitud = self._solicitudes[solicitud_id]
        return SolicitudIntervencionRead(**asdict(solicitud))

    def listar(self) -> list[SolicitudIntervencionRead]:
        return [
            SolicitudIntervencionRead(**asdict(solicitud))
            for solicitud in self._solicitudes.values()
        ]


solicitud_intervencion_service = SolicitudIntervencionService()
