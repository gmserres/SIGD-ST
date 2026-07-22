import unittest
from datetime import date
from decimal import Decimal

from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)
from app.infrastructure.database.mappers.configuracion_uc_mapper import (
    a_dominio,
    a_modelo,
    actualizar_modelo,
)


class ConfiguracionUCMapperTest(unittest.TestCase):
    def test_convierte_dominio_a_modelo_preservando_datos(self) -> None:
        configuracion = self._crear_configuracion_original()

        modelo = a_modelo(configuracion)

        self.assertEqual(modelo.id_configuracion, "configuracion-uc-1")
        self.assertEqual(modelo.valor_uc, Decimal("1677.125000"))
        self.assertEqual(modelo.fecha_inicio_vigencia, date(2026, 1, 1))
        self.assertEqual(len(modelo.rangos), 3)
        self.assertEqual(
            [rango.orden for rango in modelo.rangos],
            [0, 1, 2],
        )

    def test_convierte_modelo_a_dominio_preservando_decimal(self) -> None:
        modelo = a_modelo(self._crear_configuracion_original())

        configuracion = a_dominio(modelo)

        self.assertIsInstance(configuracion.valor_uc, Decimal)
        self.assertEqual(
            configuracion.valor_uc,
            Decimal("1677.125000"),
        )
        self.assertEqual(
            configuracion.rangos[1].limite_inferior,
            Decimal("10000"),
        )

    def test_recupera_rangos_segun_orden_persistido(self) -> None:
        modelo = a_modelo(self._crear_configuracion_original())
        modelo.rangos = list(reversed(modelo.rangos))

        configuracion = a_dominio(modelo)

        self.assertEqual(
            tuple(rango.id_rango for rango in configuracion.rangos),
            ("rango-1", "rango-2", "rango-3"),
        )

    def test_preserva_inclusividad_y_pertenencia(self) -> None:
        configuracion = a_dominio(
            a_modelo(self._crear_configuracion_original())
        )

        primer_rango = configuracion.rangos[0]
        segundo_rango = configuracion.rangos[1]

        self.assertTrue(primer_rango.limite_superior_inclusivo)
        self.assertFalse(segundo_rango.limite_inferior_inclusivo)
        self.assertEqual(
            segundo_rango.configuracion_uc_id,
            configuracion.id_configuracion,
        )

    def test_actualiza_campos_propios_del_modelo(self) -> None:
        modelo = a_modelo(self._crear_configuracion_original())
        actualizada = self._crear_configuracion_actualizada()

        actualizar_modelo(modelo, actualizada)

        self.assertEqual(
            modelo.fecha_inicio_vigencia,
            date(2026, 2, 1),
        )
        self.assertEqual(
            modelo.fecha_fin_vigencia,
            date(2026, 12, 31),
        )
        self.assertEqual(modelo.valor_uc, Decimal("1800.500000"))
        self.assertEqual(modelo.moneda, "ARS")
        self.assertEqual(modelo.resolucion, "Resolución actualizada")
        self.assertEqual(modelo.organismo_emisor, "Organismo actualizado")
        self.assertEqual(modelo.estado, "ESTADO_ACTUALIZADO")

    def test_sincroniza_coleccion_completa_reutilizando_instancias(
        self,
    ) -> None:
        modelo = a_modelo(self._crear_configuracion_original())
        rango_uno_original = modelo.rangos[0]
        rango_dos_original = modelo.rangos[1]
        rango_tres_original = modelo.rangos[2]

        actualizar_modelo(
            modelo,
            self._crear_configuracion_actualizada(),
        )

        self.assertEqual(
            [rango.id_rango for rango in modelo.rangos],
            ["rango-2", "rango-1", "rango-4"],
        )
        self.assertIs(modelo.rangos[0], rango_dos_original)
        self.assertIs(modelo.rangos[1], rango_uno_original)
        self.assertNotIn(rango_tres_original, modelo.rangos)
        self.assertEqual(
            [rango.orden for rango in modelo.rangos],
            [0, 1, 2],
        )

        primer_rango = modelo.rangos[0]
        segundo_rango = modelo.rangos[1]
        rango_nuevo = modelo.rangos[2]

        self.assertEqual(
            primer_rango.limite_inferior,
            Decimal("0"),
        )
        self.assertEqual(
            primer_rango.limite_superior,
            Decimal("20000"),
        )
        self.assertEqual(
            primer_rango.procedimiento,
            "Procedimiento actualizado",
        )
        self.assertTrue(primer_rango.limite_inferior_inclusivo)
        self.assertTrue(primer_rango.limite_superior_inclusivo)
        self.assertEqual(primer_rango.referencia_normativa, "Norma B")

        self.assertEqual(
            segundo_rango.limite_inferior,
            Decimal("20000"),
        )
        self.assertFalse(segundo_rango.limite_inferior_inclusivo)
        self.assertEqual(rango_nuevo.id_rango, "rango-4")
        self.assertEqual(
            rango_nuevo.configuracion_uc_id,
            modelo.id_configuracion,
        )

    def test_modelo_actualizado_es_convertible_a_dominio(self) -> None:
        modelo = a_modelo(self._crear_configuracion_original())
        actualizar_modelo(
            modelo,
            self._crear_configuracion_actualizada(),
        )

        configuracion = a_dominio(modelo)

        self.assertEqual(
            tuple(rango.id_rango for rango in configuracion.rangos),
            ("rango-2", "rango-1", "rango-4"),
        )
        self.assertEqual(
            configuracion.valor_uc,
            Decimal("1800.500000"),
        )
        self.assertEqual(
            configuracion.rangos[0].referencia_normativa,
            "Norma B",
        )
        self.assertTrue(
            configuracion.rangos[0].limite_superior_inclusivo
        )
        self.assertFalse(
            configuracion.rangos[1].limite_inferior_inclusivo
        )
        self.assertTrue(
            all(
                rango.configuracion_uc_id
                == configuracion.id_configuracion
                for rango in configuracion.rangos
            )
        )

    @staticmethod
    def _crear_configuracion_original() -> ConfiguracionUC:
        configuracion_id = "configuracion-uc-1"
        return ConfiguracionUC(
            id_configuracion=configuracion_id,
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=Decimal("1677.125000"),
            moneda="ARS",
            resolucion="Resolución OPC 54/2025",
            organismo_emisor="OPC",
            estado="ESTADO_DE_PRUEBA",
            rangos=(
                ConfiguracionUCMapperTest._crear_rango(
                    "rango-1", "0", "10000", True, True, "Norma A"
                ),
                ConfiguracionUCMapperTest._crear_rango(
                    "rango-2", "10000", "50000", False, True, "Norma B"
                ),
                ConfiguracionUCMapperTest._crear_rango(
                    "rango-3", "50000", "100000", False, True, "Norma C"
                ),
            ),
        )

    @staticmethod
    def _crear_configuracion_actualizada() -> ConfiguracionUC:
        configuracion_id = "configuracion-uc-1"
        return ConfiguracionUC(
            id_configuracion=configuracion_id,
            fecha_inicio_vigencia=date(2026, 2, 1),
            fecha_fin_vigencia=date(2026, 12, 31),
            valor_uc=Decimal("1800.500000"),
            moneda="ARS",
            resolucion="Resolución actualizada",
            organismo_emisor="Organismo actualizado",
            estado="ESTADO_ACTUALIZADO",
            rangos=(
                ConfiguracionUCMapperTest._crear_rango(
                    "rango-2",
                    "0",
                    "20000",
                    True,
                    True,
                    "Norma B",
                    "Procedimiento actualizado",
                ),
                ConfiguracionUCMapperTest._crear_rango(
                    "rango-1",
                    "20000",
                    "60000",
                    False,
                    True,
                    "Norma A actualizada",
                ),
                ConfiguracionUCMapperTest._crear_rango(
                    "rango-4",
                    "60000",
                    "120000",
                    False,
                    True,
                    "Norma D",
                ),
            ),
        )

    @staticmethod
    def _crear_rango(
        id_rango: str,
        limite_inferior: str,
        limite_superior: str,
        limite_inferior_inclusivo: bool,
        limite_superior_inclusivo: bool,
        referencia_normativa: str,
        procedimiento: str = "Procedimiento",
    ) -> RangoProcedimientoUC:
        return RangoProcedimientoUC(
            id_rango=id_rango,
            configuracion_uc_id="configuracion-uc-1",
            limite_inferior=Decimal(limite_inferior),
            limite_superior=Decimal(limite_superior),
            limite_inferior_inclusivo=limite_inferior_inclusivo,
            limite_superior_inclusivo=limite_superior_inclusivo,
            procedimiento=procedimiento,
            articulo="18",
            inciso="C",
            referencia_normativa=referencia_normativa,
        )


if __name__ == "__main__":
    unittest.main()
