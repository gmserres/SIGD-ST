from app.application.configuracion_uc.registrar_configuracion_uc import (
    RegistrarConfiguracionUC,
)
from app.domain.configuracion_uc import ConfiguracionUC
from app.repositories.configuracion_uc_repository import (
    ConfiguracionUCRepository,
)


class EstrategiaCargaInicialConfiguracionUC:
    def __init__(
        self,
        repository: ConfiguracionUCRepository,
        registrar_configuracion_uc: RegistrarConfiguracionUC,
    ) -> None:
        self._repository = repository
        self._registrar_configuracion_uc = registrar_configuracion_uc

    def obtener_existente(
        self,
        dato: ConfiguracionUC,
    ) -> ConfiguracionUC | None:
        return self._repository.obtener_por_id(dato.id_configuracion)

    def guardar(self, dato: ConfiguracionUC) -> None:
        self._registrar_configuracion_uc.ejecutar(dato)
