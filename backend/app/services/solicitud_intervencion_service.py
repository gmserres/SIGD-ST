from dataclasses import asdict
from uuid import uuid4

from app.domain.solicitud_intervencion import (
    NumeroSolicitudDuplicadoError,
    SolicitudIntervencion,
)
from app.repositories.solicitud_intervencion_repository import (
    SolicitudIntervencionRepository,
)
from app.schemas.solicitud_intervencion import (
    SolicitudIntervencionCreate,
    SolicitudIntervencionRead,
    SolicitudIntervencionUpdate,
)


class SolicitudIntervencionService:
    def __init__(self, repository: SolicitudIntervencionRepository) -> None:
        self._repository = repository

    def crear(
        self,
        data: SolicitudIntervencionCreate,
    ) -> SolicitudIntervencionRead:
        solicitud_existente = self._repository.obtener_por_numero(
            data.numero_solicitud
        )
        if solicitud_existente is not None:
            raise NumeroSolicitudDuplicadoError(
                "El número de solicitud ya existe."
            )

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
        self._repository.guardar(solicitud)
        return SolicitudIntervencionRead(**asdict(solicitud))

    def obtener_por_id(
        self,
        solicitud_id: str,
    ) -> SolicitudIntervencionRead:
        solicitud = self._repository.obtener_por_id(solicitud_id)
        if solicitud is None:
            raise KeyError(solicitud_id)
        return SolicitudIntervencionRead(**asdict(solicitud))

    def actualizar(
        self,
        solicitud_id: str,
        data: SolicitudIntervencionUpdate,
    ) -> SolicitudIntervencionRead:
        solicitud_existente = self._repository.obtener_por_id(
            solicitud_id
        )
        if solicitud_existente is None:
            raise KeyError(solicitud_id)

        solicitud_con_mismo_numero = (
            self._repository.obtener_por_numero(data.numero_solicitud)
        )
        if (
            solicitud_con_mismo_numero is not None
            and solicitud_con_mismo_numero.id_solicitud != solicitud_id
        ):
            raise NumeroSolicitudDuplicadoError(
                "El número de solicitud ya existe."
            )

        solicitud_actualizada = SolicitudIntervencion(
            id_solicitud=solicitud_id,
            numero_solicitud=data.numero_solicitud,
            procedencia=data.procedencia,
            id_suna=data.id_suna,
            fecha_ingreso=data.fecha_ingreso,
            establecimiento=data.establecimiento,
            solicitante=data.solicitante,
            motivo=data.motivo,
            prioridad=data.prioridad,
            estado=solicitud_existente.estado,
        )
        self._repository.guardar(solicitud_actualizada)
        return SolicitudIntervencionRead(
            **asdict(solicitud_actualizada)
        )

    def listar(self) -> list[SolicitudIntervencionRead]:
        return [
            SolicitudIntervencionRead(**asdict(solicitud))
            for solicitud in self._repository.listar()
        ]
