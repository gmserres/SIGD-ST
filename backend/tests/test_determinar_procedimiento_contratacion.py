import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app.application.configuracion_uc.determinar_procedimiento_contratacion import (
    DeterminarProcedimientoContratacion,
    MontoDeterminacionProcedimientoNegativoError,
    MultiplesRangosProcedimientoUCError,
    RangoProcedimientoUCNoEncontradoError,
)
from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ConfiguracionUCVigenteNoEncontradaError,
    SuperposicionConfiguracionesUCError,
)
from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)


class ObtenerConfiguracionUCVigenteFalso:
    def __init__(self, configuracion: ConfiguracionUC) -> None:
        self.configuracion = configuracion
        self.fechas_consultadas: list[date] = []
        self.error: Exception | None = None

    def ejecutar(self, fecha: date) -> ConfiguracionUC:
        self.fechas_consultadas.append(fecha)
        if self.error is not None:
            raise self.error
        return self.configuracion


class DeterminarProcedimientoContratacionTest(unittest.TestCase):
    def test_delega_fecha_calcula_y_conserva_resultado(self) -> None:
        fecha = date(2026, 7, 22)
        configuracion = self._crear_configuracion()
        obtener = ObtenerConfiguracionUCVigenteFalso(
            configuracion
        )
        caso_de_uso = DeterminarProcedimientoContratacion(
            obtener
        )
        monto = Decimal("12345.67")

        resultado = caso_de_uso.ejecutar(fecha, monto)

        self.assertEqual(obtener.fechas_consultadas, [fecha])
        self.assertEqual(resultado.monto, monto)
        self.assertEqual(
            resultado.cantidad_uc,
            Decimal("12.34567"),
        )
        self.assertEqual(resultado.valor_uc, Decimal("1000"))
        self.assertIs(resultado.configuracion, configuracion)
        self.assertIs(
            resultado.rango,
            configuracion.rangos[0],
        )

    def test_respeta_limite_inferior_inclusivo(self) -> None:
        configuracion = self._crear_configuracion(
            rangos=(
                self._crear_rango(
                    "rango-1",
                    Decimal("10"),
                    Decimal("20"),
                    inferior_inclusivo=True,
                    superior_inclusivo=True,
                ),
            )
        )

        resultado = self._ejecutar(
            configuracion,
            Decimal("10000"),
        )

        self.assertEqual(resultado.rango.id_rango, "rango-1")

    def test_respeta_limite_inferior_exclusivo(self) -> None:
        configuracion = self._crear_configuracion(
            rangos=(
                self._crear_rango(
                    "rango-1",
                    Decimal("10"),
                    Decimal("20"),
                    inferior_inclusivo=False,
                    superior_inclusivo=True,
                ),
            )
        )

        with self.assertRaises(
            RangoProcedimientoUCNoEncontradoError
        ):
            self._ejecutar(configuracion, Decimal("10000"))

    def test_respeta_limite_superior_inclusivo(self) -> None:
        configuracion = self._crear_configuracion(
            rangos=(
                self._crear_rango(
                    "rango-1",
                    Decimal("0"),
                    Decimal("20"),
                    inferior_inclusivo=True,
                    superior_inclusivo=True,
                ),
            )
        )

        resultado = self._ejecutar(
            configuracion,
            Decimal("20000"),
        )

        self.assertEqual(resultado.rango.id_rango, "rango-1")

    def test_respeta_limite_superior_exclusivo(self) -> None:
        configuracion = self._crear_configuracion(
            rangos=(
                self._crear_rango(
                    "rango-1",
                    Decimal("0"),
                    Decimal("20"),
                    inferior_inclusivo=True,
                    superior_inclusivo=False,
                ),
            )
        )

        with self.assertRaises(
            RangoProcedimientoUCNoEncontradoError
        ):
            self._ejecutar(configuracion, Decimal("20000"))

    def test_no_depende_del_orden_recibido_de_los_rangos(
        self,
    ) -> None:
        segundo = self._crear_rango(
            "rango-2",
            Decimal("100"),
            Decimal("200"),
            inferior_inclusivo=False,
            superior_inclusivo=True,
        )
        primero = self._crear_rango(
            "rango-1",
            Decimal("0"),
            Decimal("100"),
            inferior_inclusivo=True,
            superior_inclusivo=True,
        )
        configuracion = self._crear_configuracion(
            rangos=(segundo, primero)
        )

        resultado = self._ejecutar(
            configuracion,
            Decimal("150000"),
        )

        self.assertEqual(resultado.rango.id_rango, "rango-2")

    def test_informa_ausencia_de_rango(self) -> None:
        configuracion = self._crear_configuracion(
            rangos=(
                self._crear_rango(
                    "rango-1",
                    Decimal("10"),
                    Decimal("20"),
                ),
            )
        )

        with self.assertRaises(
            RangoProcedimientoUCNoEncontradoError
        ) as contexto:
            self._ejecutar(configuracion, Decimal("25000"))

        self.assertEqual(
            contexto.exception.cantidad_uc,
            Decimal("25"),
        )
        self.assertEqual(
            contexto.exception.configuracion_id,
            "configuracion-1",
        )
        self.assertIn(
            "configuracion-1",
            str(contexto.exception),
        )

    def test_informa_todos_los_rangos_coincidentes(self) -> None:
        configuracion = self._crear_configuracion()
        obtener = ObtenerConfiguracionUCVigenteFalso(
            configuracion
        )
        caso_de_uso = DeterminarProcedimientoContratacion(
            obtener
        )

        with patch.object(
            DeterminarProcedimientoContratacion,
            "_contiene",
            return_value=True,
        ):
            with self.assertRaises(
                MultiplesRangosProcedimientoUCError
            ) as contexto:
                caso_de_uso.ejecutar(
                    date(2026, 7, 22),
                    Decimal("50000"),
                )

        self.assertEqual(
            contexto.exception.cantidad_uc,
            Decimal("50"),
        )
        self.assertEqual(
            contexto.exception.configuracion_id,
            "configuracion-1",
        )
        self.assertEqual(
            contexto.exception.rango_ids,
            ("rango-1", "rango-2"),
        )
        self.assertIn("rango-1", str(contexto.exception))
        self.assertIn("rango-2", str(contexto.exception))

    def test_propaga_ausencia_de_configuracion(self) -> None:
        fecha = date(2026, 7, 22)
        error = ConfiguracionUCVigenteNoEncontradaError(fecha)

        error_obtenido = self._ejecutar_con_error(error)

        self.assertIs(error_obtenido, error)

    def test_propaga_superposicion_de_configuraciones(
        self,
    ) -> None:
        fecha = date(2026, 7, 22)
        error = SuperposicionConfiguracionesUCError(
            fecha,
            ("configuracion-1", "configuracion-2"),
        )

        error_obtenido = self._ejecutar_con_error(error)

        self.assertIs(error_obtenido, error)

    def test_propaga_error_tecnico(self) -> None:
        error = RuntimeError("Error técnico controlado.")

        error_obtenido = self._ejecutar_con_error(error)

        self.assertIs(error_obtenido, error)

    def test_rechaza_monto_negativo_sin_consultar_configuracion(
        self,
    ) -> None:
        configuracion = self._crear_configuracion()
        obtener = ObtenerConfiguracionUCVigenteFalso(
            configuracion
        )
        caso_de_uso = DeterminarProcedimientoContratacion(
            obtener
        )

        with self.assertRaises(
            MontoDeterminacionProcedimientoNegativoError
        ) as contexto:
            caso_de_uso.ejecutar(
                date(2026, 7, 22),
                Decimal("-0.01"),
            )

        self.assertEqual(
            contexto.exception.monto,
            Decimal("-0.01"),
        )
        self.assertEqual(obtener.fechas_consultadas, [])

    def test_evalua_monto_cero_contra_los_rangos(self) -> None:
        configuracion = self._crear_configuracion()

        resultado = self._ejecutar(
            configuracion,
            Decimal("0"),
        )

        self.assertEqual(resultado.cantidad_uc, Decimal("0"))
        self.assertEqual(resultado.rango.id_rango, "rango-1")

    def _ejecutar(
        self,
        configuracion: ConfiguracionUC,
        monto: Decimal,
    ):
        obtener = ObtenerConfiguracionUCVigenteFalso(
            configuracion
        )
        return DeterminarProcedimientoContratacion(
            obtener
        ).ejecutar(date(2026, 7, 22), monto)

    def _ejecutar_con_error(
        self,
        error: Exception,
    ) -> Exception:
        obtener = ObtenerConfiguracionUCVigenteFalso(
            self._crear_configuracion()
        )
        obtener.error = error
        caso_de_uso = DeterminarProcedimientoContratacion(
            obtener
        )

        with self.assertRaises(type(error)) as contexto:
            caso_de_uso.ejecutar(
                date(2026, 7, 22),
                Decimal("50000"),
            )

        return contexto.exception

    def _crear_configuracion(
        self,
        rangos: tuple[RangoProcedimientoUC, ...] | None = None,
    ) -> ConfiguracionUC:
        return ConfiguracionUC(
            id_configuracion="configuracion-1",
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=Decimal("1000"),
            moneda="MONEDA_DE_PRUEBA",
            resolucion="RESOLUCION_DE_PRUEBA",
            organismo_emisor="ORGANISMO_DE_PRUEBA",
            estado="ESTADO_DE_PRUEBA",
            rangos=rangos or (
                self._crear_rango(
                    "rango-1",
                    Decimal("0"),
                    Decimal("100"),
                    inferior_inclusivo=True,
                    superior_inclusivo=True,
                ),
                self._crear_rango(
                    "rango-2",
                    Decimal("100"),
                    Decimal("200"),
                    inferior_inclusivo=False,
                    superior_inclusivo=True,
                ),
            ),
        )

    @staticmethod
    def _crear_rango(
        rango_id: str,
        limite_inferior: Decimal,
        limite_superior: Decimal,
        inferior_inclusivo: bool = True,
        superior_inclusivo: bool = True,
    ) -> RangoProcedimientoUC:
        return RangoProcedimientoUC(
            id_rango=rango_id,
            configuracion_uc_id="configuracion-1",
            limite_inferior=limite_inferior,
            limite_superior=limite_superior,
            limite_inferior_inclusivo=inferior_inclusivo,
            limite_superior_inclusivo=superior_inclusivo,
            procedimiento="PROCEDIMIENTO_DE_PRUEBA",
            articulo="ARTICULO_DE_PRUEBA",
            inciso="INCISO_DE_PRUEBA",
            referencia_normativa="REFERENCIA_DE_PRUEBA",
        )


if __name__ == "__main__":
    unittest.main()
