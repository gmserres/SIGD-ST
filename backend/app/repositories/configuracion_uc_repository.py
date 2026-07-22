from datetime import date
from typing import Protocol

from app.domain.configuracion_uc import ConfiguracionUC, ConfiguracionUCId


class ConfiguracionUCRepository(Protocol):
    def guardar(self, configuracion: ConfiguracionUC) -> None:
        ...

    def obtener_por_id(
        self,
        configuracion_id: ConfiguracionUCId,
    ) -> ConfiguracionUC | None:
        ...

    def listar(self) -> list[ConfiguracionUC]:
        ...

    def buscar_vigentes_para_fecha(
        self,
        fecha: date,
    ) -> list[ConfiguracionUC]:
        ...
