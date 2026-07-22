from enum import Enum
from typing import Protocol, TypeVar


T = TypeVar("T")


class ResultadoCargaInicial(str, Enum):
    CARGADA = "CARGADA"
    YA_EXISTENTE = "YA_EXISTENTE"


class CargaInicialDivergenteError(RuntimeError):
    def __init__(self, nombre_carga: str) -> None:
        self.nombre_carga = nombre_carga
        super().__init__(
            f"La carga inicial '{nombre_carga}' ya existe con datos diferentes."
        )


class EstrategiaCargaInicial(Protocol[T]):
    def obtener_existente(self, dato: T) -> T | None:
        ...

    def guardar(self, dato: T) -> None:
        ...


def ejecutar_carga_inicial(
    *,
    nombre_carga: str,
    dato: T,
    estrategia: EstrategiaCargaInicial[T],
) -> ResultadoCargaInicial:
    existente = estrategia.obtener_existente(dato)

    if existente is None:
        estrategia.guardar(dato)
        return ResultadoCargaInicial.CARGADA

    if existente == dato:
        return ResultadoCargaInicial.YA_EXISTENTE

    raise CargaInicialDivergenteError(nombre_carga)
