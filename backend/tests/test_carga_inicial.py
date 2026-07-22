import unittest
from dataclasses import dataclass

from app.initial_data.carga_inicial import (
    CargaInicialDivergenteError,
    ResultadoCargaInicial,
    ejecutar_carga_inicial,
)


@dataclass(frozen=True)
class DatoInicialPrueba:
    identificador: str
    valor: str


class EstrategiaCargaInicialFalsa:
    def __init__(
        self,
        existente: DatoInicialPrueba | None = None,
    ) -> None:
        self.existente = existente
        self.guardados: list[DatoInicialPrueba] = []

    def obtener_existente(
        self,
        dato: DatoInicialPrueba,
    ) -> DatoInicialPrueba | None:
        return self.existente

    def guardar(self, dato: DatoInicialPrueba) -> None:
        self.guardados.append(dato)
        self.existente = dato


class EstrategiaCargaInicialConError(EstrategiaCargaInicialFalsa):
    def guardar(self, dato: DatoInicialPrueba) -> None:
        raise RuntimeError("Fallo controlado de persistencia.")


class CargaInicialTest(unittest.TestCase):
    def test_guarda_cuando_la_carga_no_existe(self) -> None:
        dato = DatoInicialPrueba("dato-1", "valor")
        estrategia = EstrategiaCargaInicialFalsa()

        resultado = ejecutar_carga_inicial(
            nombre_carga="Carga de prueba",
            dato=dato,
            estrategia=estrategia,
        )

        self.assertEqual(resultado, ResultadoCargaInicial.CARGADA)
        self.assertEqual(estrategia.guardados, [dato])

    def test_no_escribe_si_la_carga_existente_es_identica(self) -> None:
        dato = DatoInicialPrueba("dato-1", "valor")
        estrategia = EstrategiaCargaInicialFalsa(dato)

        resultado = ejecutar_carga_inicial(
            nombre_carga="Carga de prueba",
            dato=dato,
            estrategia=estrategia,
        )

        self.assertEqual(
            resultado,
            ResultadoCargaInicial.YA_EXISTENTE,
        )
        self.assertEqual(estrategia.guardados, [])

    def test_rechaza_una_carga_existente_divergente(self) -> None:
        estrategia = EstrategiaCargaInicialFalsa(
            DatoInicialPrueba("dato-1", "original")
        )

        with self.assertRaisesRegex(
            CargaInicialDivergenteError,
            "Carga de prueba",
        ):
            ejecutar_carga_inicial(
                nombre_carga="Carga de prueba",
                dato=DatoInicialPrueba("dato-1", "diferente"),
                estrategia=estrategia,
            )

        self.assertEqual(estrategia.guardados, [])
        self.assertEqual(estrategia.existente.valor, "original")

    def test_propaga_el_error_de_persistencia(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "Fallo controlado de persistencia",
        ):
            ejecutar_carga_inicial(
                nombre_carga="Carga de prueba",
                dato=DatoInicialPrueba("dato-1", "valor"),
                estrategia=EstrategiaCargaInicialConError(),
            )

    def test_segunda_ejecucion_no_realiza_otra_escritura(self) -> None:
        dato = DatoInicialPrueba("dato-1", "valor")
        estrategia = EstrategiaCargaInicialFalsa()

        ejecutar_carga_inicial(
            nombre_carga="Carga de prueba",
            dato=dato,
            estrategia=estrategia,
        )
        resultado = ejecutar_carga_inicial(
            nombre_carga="Carga de prueba",
            dato=dato,
            estrategia=estrategia,
        )

        self.assertEqual(
            resultado,
            ResultadoCargaInicial.YA_EXISTENTE,
        )
        self.assertEqual(len(estrategia.guardados), 1)


if __name__ == "__main__":
    unittest.main()
