import unittest
from datetime import date
from decimal import Decimal

from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ConfiguracionUCVigenteNoEncontradaError,
    FechaConsultaConfiguracionUCRequeridaError,
    ObtenerConfiguracionUCVigente,
    SuperposicionConfiguracionesUCError,
)
from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)


class RepositorioConfiguracionUCConsultaFalso:
    def __init__(
        self,
        resultados: list[ConfiguracionUC] | None = None,
    ) -> None:
        self.resultados = list(resultados or [])
        self.fechas_consultadas: list[date] = []
        self.error: Exception | None = None

    def buscar_vigentes_para_fecha(
        self,
        fecha: date,
    ) -> list[ConfiguracionUC]:
        self.fechas_consultadas.append(fecha)
        if self.error is not None:
            raise self.error
        return list(self.resultados)


class ObtenerConfiguracionUCVigenteTest(unittest.TestCase):
    def test_delega_fecha_y_devuelve_unica_coincidencia(self) -> None:
        fecha = date(2026, 7, 22)
        configuracion = self._crear_configuracion(
            "configuracion-1"
        )
        repository = RepositorioConfiguracionUCConsultaFalso(
            [configuracion]
        )
        caso_de_uso = ObtenerConfiguracionUCVigente(repository)

        resultado = caso_de_uso.ejecutar(fecha)

        self.assertEqual(resultado, configuracion)
        self.assertEqual(repository.fechas_consultadas, [fecha])

    def test_rechaza_cero_coincidencias(self) -> None:
        fecha = date(2026, 7, 22)
        repository = RepositorioConfiguracionUCConsultaFalso()
        caso_de_uso = ObtenerConfiguracionUCVigente(repository)

        with self.assertRaises(
            ConfiguracionUCVigenteNoEncontradaError
        ) as contexto:
            caso_de_uso.ejecutar(fecha)

        self.assertEqual(contexto.exception.fecha, fecha)
        self.assertIn(fecha.isoformat(), str(contexto.exception))

    def test_rechaza_multiples_coincidencias_sin_seleccionar(
        self,
    ) -> None:
        fecha = date(2026, 7, 22)
        primera = self._crear_configuracion("configuracion-1")
        segunda = self._crear_configuracion("configuracion-2")
        repository = RepositorioConfiguracionUCConsultaFalso(
            [primera, segunda]
        )
        caso_de_uso = ObtenerConfiguracionUCVigente(repository)

        with self.assertRaises(
            SuperposicionConfiguracionesUCError
        ) as contexto:
            caso_de_uso.ejecutar(fecha)

        self.assertEqual(contexto.exception.fecha, fecha)
        self.assertEqual(
            contexto.exception.configuracion_ids,
            ("configuracion-1", "configuracion-2"),
        )
        self.assertIn("configuracion-1", str(contexto.exception))
        self.assertIn("configuracion-2", str(contexto.exception))

    def test_rechaza_fecha_ausente_sin_consultar_repositorio(
        self,
    ) -> None:
        repository = RepositorioConfiguracionUCConsultaFalso()
        caso_de_uso = ObtenerConfiguracionUCVigente(repository)

        with self.assertRaises(
            FechaConsultaConfiguracionUCRequeridaError
        ):
            caso_de_uso.ejecutar(None)

        self.assertEqual(repository.fechas_consultadas, [])

    def test_propaga_error_tecnico_del_repositorio(self) -> None:
        repository = RepositorioConfiguracionUCConsultaFalso()
        repository.error = RuntimeError("Error técnico controlado.")
        caso_de_uso = ObtenerConfiguracionUCVigente(repository)

        with self.assertRaisesRegex(
            RuntimeError,
            "Error técnico controlado",
        ):
            caso_de_uso.ejecutar(date(2026, 7, 22))

    @staticmethod
    def _crear_configuracion(
        configuracion_id: str,
    ) -> ConfiguracionUC:
        return ConfiguracionUC(
            id_configuracion=configuracion_id,
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=Decimal("1000"),
            moneda="MONEDA_DE_PRUEBA",
            resolucion=f"Resolución {configuracion_id}",
            organismo_emisor="ORGANISMO_DE_PRUEBA",
            estado="ESTADO_DE_PRUEBA",
            rangos=(
                RangoProcedimientoUC(
                    id_rango=f"{configuracion_id}-rango",
                    configuracion_uc_id=configuracion_id,
                    limite_inferior=Decimal("0"),
                    limite_superior=Decimal("100"),
                    limite_inferior_inclusivo=True,
                    limite_superior_inclusivo=True,
                    procedimiento="PROCEDIMIENTO_DE_PRUEBA",
                    articulo="ARTICULO_DE_PRUEBA",
                    inciso="INCISO_DE_PRUEBA",
                    referencia_normativa="REFERENCIA_DE_PRUEBA",
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
