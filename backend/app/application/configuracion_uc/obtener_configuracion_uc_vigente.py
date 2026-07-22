from datetime import date

from app.domain.configuracion_uc import (
    ConfiguracionUC,
    ConfiguracionUCId,
)
from app.repositories.configuracion_uc_repository import (
    ConfiguracionUCRepository,
)


class FechaConsultaConfiguracionUCRequeridaError(ValueError):
    pass


class ConfiguracionUCVigenteNoEncontradaError(LookupError):
    def __init__(self, fecha: date) -> None:
        self.fecha = fecha
        super().__init__(
            "No existe una Configuración UC vigente para la fecha "
            f"{fecha.isoformat()}."
        )


class SuperposicionConfiguracionesUCError(ValueError):
    def __init__(
        self,
        fecha: date,
        configuracion_ids: tuple[ConfiguracionUCId, ...],
    ) -> None:
        self.fecha = fecha
        self.configuracion_ids = configuracion_ids
        identificadores = ", ".join(
            str(configuracion_id)
            for configuracion_id in configuracion_ids
        )
        super().__init__(
            "Existe más de una Configuración UC vigente para la fecha "
            f"{fecha.isoformat()}: {identificadores}."
        )


class ObtenerConfiguracionUCVigente:
    def __init__(
        self,
        repository: ConfiguracionUCRepository,
    ) -> None:
        self._repository = repository

    def ejecutar(
        self,
        fecha: date | None,
    ) -> ConfiguracionUC:
        if fecha is None:
            raise FechaConsultaConfiguracionUCRequeridaError(
                "La fecha de consulta de Configuración UC es obligatoria."
            )

        configuraciones = (
            self._repository.buscar_vigentes_para_fecha(fecha)
        )

        if not configuraciones:
            raise ConfiguracionUCVigenteNoEncontradaError(fecha)

        if len(configuraciones) > 1:
            raise SuperposicionConfiguracionesUCError(
                fecha,
                tuple(
                    configuracion.id_configuracion
                    for configuracion in configuraciones
                ),
            )

        return configuraciones[0]
