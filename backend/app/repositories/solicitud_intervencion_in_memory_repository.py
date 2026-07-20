from app.domain.solicitud_intervencion import (
    NumeroSolicitudDuplicadoError,
    SolicitudIntervencion,
)


class InMemorySolicitudIntervencionRepository:
    def __init__(self) -> None:
        self._solicitudes: dict[str, SolicitudIntervencion] = {}

    def guardar(self, solicitud: SolicitudIntervencion) -> None:
        existente = self.obtener_por_numero(solicitud.numero_solicitud)
        if (
            existente is not None
            and existente.id_solicitud != solicitud.id_solicitud
        ):
            raise NumeroSolicitudDuplicadoError(
                "El número de solicitud ya existe."
            )
        self._solicitudes[solicitud.id_solicitud] = solicitud

    def obtener_por_id(
        self,
        solicitud_id: str,
    ) -> SolicitudIntervencion | None:
        return self._solicitudes.get(solicitud_id)

    def obtener_por_numero(
        self,
        numero_solicitud: str,
    ) -> SolicitudIntervencion | None:
        return next(
            (
                solicitud
                for solicitud in self._solicitudes.values()
                if solicitud.numero_solicitud == numero_solicitud
            ),
            None,
        )

    def listar(
        self,
        *,
        numero_solicitud: str | None = None,
        id_suna: str | None = None,
        procedencia: str | None = None,
        establecimiento: str | None = None,
        estado: str | None = None,
    ) -> list[SolicitudIntervencion]:
        solicitudes = list(self._solicitudes.values())

        return [
            solicitud
            for solicitud in solicitudes
            if (
                numero_solicitud is None
                or solicitud.numero_solicitud == numero_solicitud
            )
            and (
                id_suna is None
                or solicitud.id_suna == id_suna
            )
            and (
                procedencia is None
                or solicitud.procedencia.casefold()
                == procedencia.casefold()
            )
            and (
                establecimiento is None
                or establecimiento.casefold()
                in solicitud.establecimiento.casefold()
            )
            and (
                estado is None
                or solicitud.estado.casefold() == estado.casefold()
            )
        ]
