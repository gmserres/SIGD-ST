import unittest
from datetime import date
from decimal import Decimal

from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
    VigenciaConfiguracionUCSuperpuestaError,
    validar_vigencias_no_superpuestas,
)


class ConfiguracionUCVigenciasTest(unittest.TestCase):
    def test_admite_varias_configuraciones_en_el_mismo_anio(
        self,
    ) -> None:
        primera = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            date(2026, 6, 30),
        )
        segunda = self._crear_configuracion(
            "configuracion-2",
            date(2026, 7, 1),
            None,
        )

        validar_vigencias_no_superpuestas(segunda, [primera])

    def test_admite_vigencias_consecutivas(self) -> None:
        anterior = self._crear_configuracion(
            "configuracion-1",
            date(2026, 3, 1),
            date(2026, 10, 14),
        )
        posterior = self._crear_configuracion(
            "configuracion-2",
            date(2026, 10, 15),
            None,
        )

        validar_vigencias_no_superpuestas(posterior, [anterior])

    def test_rechaza_fecha_compartida_por_periodos_inclusivos(
        self,
    ) -> None:
        existente = self._crear_configuracion(
            "configuracion-1",
            date(2026, 3, 1),
            date(2026, 10, 14),
        )
        superpuesta = self._crear_configuracion(
            "configuracion-2",
            date(2026, 10, 14),
            None,
        )

        with self.assertRaises(
            VigenciaConfiguracionUCSuperpuestaError
        ):
            validar_vigencias_no_superpuestas(
                superpuesta,
                [existente],
            )

    def test_vigencia_abierta_se_superpone_con_periodo_posterior(
        self,
    ) -> None:
        abierta = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            None,
        )
        posterior = self._crear_configuracion(
            "configuracion-2",
            date(2027, 1, 1),
            None,
        )

        with self.assertRaises(
            VigenciaConfiguracionUCSuperpuestaError
        ):
            validar_vigencias_no_superpuestas(
                posterior,
                [abierta],
            )

    def test_ignora_la_misma_identidad_tecnica(self) -> None:
        configuracion = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            None,
        )

        validar_vigencias_no_superpuestas(
            configuracion,
            [configuracion],
        )

    @staticmethod
    def _crear_configuracion(
        configuracion_id: str,
        fecha_inicio: date,
        fecha_fin: date | None,
    ) -> ConfiguracionUC:
        return ConfiguracionUC(
            id_configuracion=configuracion_id,
            fecha_inicio_vigencia=fecha_inicio,
            fecha_fin_vigencia=fecha_fin,
            valor_uc=Decimal("1000"),
            moneda="MONEDA_DE_PRUEBA",
            resolucion="Resolución de prueba",
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
