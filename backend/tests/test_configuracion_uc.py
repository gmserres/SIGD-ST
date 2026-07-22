import unittest
from datetime import date
from decimal import Decimal

from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)
from app.schemas.configuracion_uc import ConfiguracionUCSchema


class ConfiguracionUCTest(unittest.TestCase):
    def test_crea_configuracion_con_rangos_continuos(self) -> None:
        configuracion = self._crear_configuracion()

        self.assertEqual(configuracion.valor_uc, Decimal("1677"))
        self.assertEqual(len(configuracion.rangos), 3)

    def test_identidades_se_representan_como_cadenas(self) -> None:
        configuracion = self._crear_configuracion()
        schema = ConfiguracionUCSchema.model_validate(configuracion)
        serializado = schema.model_dump(mode="json")

        self.assertIsInstance(configuracion.id_configuracion, str)
        self.assertIsInstance(configuracion.rangos[0].id_rango, str)
        self.assertEqual(
            serializado["id_configuracion"],
            "configuracion-uc-1",
        )
        self.assertEqual(
            serializado["rangos"][0]["configuracion_uc_id"],
            "configuracion-uc-1",
        )

    def test_ordena_rangos_validos_recibidos_desordenados(self) -> None:
        rangos = self._rangos_validos()
        configuracion = self._crear_configuracion(
            rangos=(rangos[2], rangos[0], rangos[1]),
        )

        self.assertEqual(
            tuple(rango.id_rango for rango in configuracion.rangos),
            ("rango-1", "rango-2", "rango-3"),
        )
        self.assertEqual(
            tuple(rango.limite_inferior for rango in configuracion.rangos),
            (
                Decimal("0"),
                Decimal("10000"),
                Decimal("50000"),
            ),
        )

    def test_rechaza_valor_uc_no_positivo(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "El valor UC debe ser mayor que cero.",
        ):
            self._crear_configuracion(valor_uc=Decimal("0"))

    def test_rechaza_fecha_final_anterior_a_inicial(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "La fecha de fin de vigencia no puede ser anterior",
        ):
            self._crear_configuracion(
                fecha_inicio=date(2026, 2, 1),
                fecha_fin=date(2026, 1, 31),
            )

    def test_rechaza_resolucion_vacia(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "La resolución es obligatoria.",
        ):
            self._crear_configuracion(resolucion=" ")

    def test_acepta_resolucion_como_texto_libre(self) -> None:
        configuracion = self._crear_configuracion(
            resolucion="Resolución histórica de referencia"
        )

        self.assertEqual(
            configuracion.resolucion,
            "Resolución histórica de referencia",
        )

    def test_rechaza_organismo_emisor_vacio(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "El organismo emisor es obligatorio.",
        ):
            self._crear_configuracion(organismo_emisor="")

    def test_rechaza_estado_vacio(self) -> None:
        with self.assertRaisesRegex(ValueError, "El estado es obligatorio."):
            self._crear_configuracion(estado="   ")

    def test_acepta_estado_sin_catalogo_cerrado(self) -> None:
        configuracion = self._crear_configuracion(
            estado="ESTADO_DE_PRUEBA",
        )

        self.assertEqual(configuracion.estado, "ESTADO_DE_PRUEBA")

    def test_rechaza_configuracion_sin_rangos(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "debe contener al menos un rango",
        ):
            self._crear_configuracion(rangos=())

    def test_rechaza_rango_con_limites_incoherentes(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "El límite superior debe ser mayor",
        ):
            self._crear_rango(
                "rango-1",
                Decimal("10000"),
                Decimal("10000"),
                True,
                True,
            )

    def test_rechaza_rangos_superpuestos_aunque_estén_desordenados(
        self,
    ) -> None:
        rangos = (
            self._crear_rango(
                "rango-2",
                Decimal("9000"),
                Decimal("50000"),
                False,
                True,
            ),
            self._crear_rango(
                "rango-1",
                Decimal("0"),
                Decimal("10000"),
                True,
                True,
            ),
        )

        with self.assertRaisesRegex(ValueError, "no pueden superponerse"):
            self._crear_configuracion(rangos=rangos)

    def test_rechaza_discontinuidad_aunque_estén_desordenados(self) -> None:
        rangos = (
            self._crear_rango(
                "rango-2",
                Decimal("10001"),
                Decimal("50000"),
                True,
                True,
            ),
            self._crear_rango(
                "rango-1",
                Decimal("0"),
                Decimal("10000"),
                True,
                True,
            ),
        )

        with self.assertRaisesRegex(ValueError, "deben ser continuos"):
            self._crear_configuracion(rangos=rangos)

    def test_rechaza_limite_incluido_en_dos_rangos(self) -> None:
        rangos = (
            self._crear_rango(
                "rango-1",
                Decimal("0"),
                Decimal("10000"),
                True,
                True,
            ),
            self._crear_rango(
                "rango-2",
                Decimal("10000"),
                Decimal("50000"),
                True,
                True,
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "no puede pertenecer a dos rangos",
        ):
            self._crear_configuracion(rangos=rangos)

    def test_rechaza_limite_excluido_de_ambos_rangos(self) -> None:
        rangos = (
            self._crear_rango(
                "rango-1",
                Decimal("0"),
                Decimal("10000"),
                True,
                False,
            ),
            self._crear_rango(
                "rango-2",
                Decimal("10000"),
                Decimal("50000"),
                False,
                True,
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "debe pertenecer a uno de los rangos",
        ):
            self._crear_configuracion(rangos=rangos)

    def test_rechaza_rango_de_otra_configuracion(self) -> None:
        rango = RangoProcedimientoUC(
            id_rango="rango-externo",
            configuracion_uc_id="otra-configuracion",
            limite_inferior=Decimal("0"),
            limite_superior=Decimal("10000"),
            limite_inferior_inclusivo=True,
            limite_superior_inclusivo=True,
            procedimiento="Factura Conformada",
            articulo="18",
            inciso="C",
            referencia_normativa="Ley 13.981",
        )

        with self.assertRaisesRegex(
            ValueError,
            "pertenecer exclusivamente",
        ):
            self._crear_configuracion(rangos=(rango,))

    def test_schema_representa_el_agregado(self) -> None:
        configuracion = self._crear_configuracion()

        schema = ConfiguracionUCSchema.model_validate(configuracion)

        self.assertEqual(schema.id_configuracion, "configuracion-uc-1")
        self.assertEqual(schema.valor_uc, Decimal("1677"))
        self.assertEqual(len(schema.rangos), 3)

    def _crear_configuracion(
        self,
        *,
        valor_uc: Decimal = Decimal("1677"),
        fecha_inicio: date = date(2026, 1, 1),
        fecha_fin: date | None = None,
        resolucion: str = "Resolución de prueba",
        organismo_emisor: str = "OPC",
        estado: str = "ESTADO_DE_PRUEBA",
        rangos: tuple[RangoProcedimientoUC, ...] | None = None,
    ) -> ConfiguracionUC:
        return ConfiguracionUC(
            id_configuracion="configuracion-uc-1",
            fecha_inicio_vigencia=fecha_inicio,
            fecha_fin_vigencia=fecha_fin,
            valor_uc=valor_uc,
            moneda="ARS",
            resolucion=resolucion,
            organismo_emisor=organismo_emisor,
            estado=estado,
            rangos=rangos if rangos is not None else self._rangos_validos(),
        )

    def _rangos_validos(self) -> tuple[RangoProcedimientoUC, ...]:
        return (
            self._crear_rango(
                "rango-1",
                Decimal("0"),
                Decimal("10000"),
                True,
                True,
            ),
            self._crear_rango(
                "rango-2",
                Decimal("10000"),
                Decimal("50000"),
                False,
                True,
            ),
            self._crear_rango(
                "rango-3",
                Decimal("50000"),
                Decimal("100000"),
                False,
                True,
            ),
        )

    @staticmethod
    def _crear_rango(
        id_rango: str,
        limite_inferior: Decimal,
        limite_superior: Decimal,
        limite_inferior_inclusivo: bool,
        limite_superior_inclusivo: bool,
    ) -> RangoProcedimientoUC:
        return RangoProcedimientoUC(
            id_rango=id_rango,
            configuracion_uc_id="configuracion-uc-1",
            limite_inferior=limite_inferior,
            limite_superior=limite_superior,
            limite_inferior_inclusivo=limite_inferior_inclusivo,
            limite_superior_inclusivo=limite_superior_inclusivo,
            procedimiento="Procedimiento",
            articulo="18",
            inciso="C",
            referencia_normativa="Ley 13.981",
        )


if __name__ == "__main__":
    unittest.main()
