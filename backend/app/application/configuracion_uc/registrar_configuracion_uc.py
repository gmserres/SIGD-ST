from app.domain.configuracion_uc import (
    ConfiguracionUC,
    validar_vigencias_no_superpuestas,
)
from app.repositories.configuracion_uc_repository import (
    ConfiguracionUCRepository,
)


class ConfiguracionUCYaRegistradaError(ValueError):
    pass


class RegistrarConfiguracionUC:
    def __init__(
        self,
        repository: ConfiguracionUCRepository,
    ) -> None:
        self._repository = repository

    def ejecutar(
        self,
        configuracion: ConfiguracionUC,
    ) -> ConfiguracionUC:
        existente = self._repository.obtener_por_id(
            configuracion.id_configuracion
        )
        if existente is not None:
            raise ConfiguracionUCYaRegistradaError(
                "La Configuración UC ya se encuentra registrada."
            )

        existentes = self._repository.listar()
        validar_vigencias_no_superpuestas(
            configuracion,
            existentes,
        )
        self._repository.guardar(configuracion)
        return configuracion
