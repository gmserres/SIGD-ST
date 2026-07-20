from typing import Protocol

from app.domain.solicitud_intervencion import SolicitudIntervencion


class SolicitudIntervencionRepository(Protocol):
    def guardar(self, solicitud: SolicitudIntervencion) -> None:
        ...

    def obtener_por_id(
        self,
        solicitud_id: str,
    ) -> SolicitudIntervencion | None:
        ...

    def obtener_por_numero(
        self,
        numero_solicitud: str,
    ) -> SolicitudIntervencion | None:
        ...

    def listar(
        self,
        *,
        numero_solicitud: str | None = None,
        id_suna: str | None = None,
        procedencia: str | None = None,
        establecimiento: str | None = None,
        estado: str | None = None,
    ) -> list[SolicitudIntervencion]:
        ...
