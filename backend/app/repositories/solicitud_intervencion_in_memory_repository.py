from app.domain.solicitud_intervencion import SolicitudIntervencion


class InMemorySolicitudIntervencionRepository:
    def __init__(self) -> None:
        self._solicitudes: dict[str, SolicitudIntervencion] = {}

    def guardar(self, solicitud: SolicitudIntervencion) -> None:
        self._solicitudes[solicitud.id_solicitud] = solicitud

    def obtener_por_id(
        self,
        solicitud_id: str,
    ) -> SolicitudIntervencion | None:
        return self._solicitudes.get(solicitud_id)

    def listar(self) -> list[SolicitudIntervencion]:
        return list(self._solicitudes.values())
