import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app.application.configuracion_uc.registrar_configuracion_uc import (
    RegistrarConfiguracionUC,
)
from app.application.initial_data.configuracion_uc_strategy import (
    EstrategiaCargaInicialConfiguracionUC,
)
from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)
from app.initial_data.carga_inicial import (
    CargaInicialDivergenteError,
    ResultadoCargaInicial,
    ejecutar_carga_inicial,
)
from app.initial_data.configuracion_uc_inicial import (
    CONFIGURACION_UC_INICIAL_ID,
    DatosNormativosPendientesError,
    crear_configuracion_uc_inicial,
)


class RepositorioConfiguracionUCFalso:
    def __init__(
        self,
        existente: ConfiguracionUC | None = None,
    ) -> None:
        self.existente = existente
        self.guardados: list[ConfiguracionUC] = []

    def guardar(self, configuracion: ConfiguracionUC) -> None:
        self.guardados.append(configuracion)
        self.existente = configuracion

    def obtener_por_id(
        self,
        configuracion_id: str,
    ) -> ConfiguracionUC | None:
        if (
            self.existente is not None
            and self.existente.id_configuracion == configuracion_id
        ):
            return self.existente
        return None

    def listar(self) -> list[ConfiguracionUC]:
        return [self.existente] if self.existente is not None else []

    def buscar_vigentes_para_fecha(
        self,
        fecha: date,
    ) -> list[ConfiguracionUC]:
        return []


class ConfiguracionUCInicialTest(unittest.TestCase):
    def test_identificador_inicial_es_estable(self) -> None:
        self.assertEqual(
            CONFIGURACION_UC_INICIAL_ID,
            "configuracion-uc-carga-001",
        )
        self.assertLessEqual(len(CONFIGURACION_UC_INICIAL_ID), 64)

    def test_bloquea_datos_normativos_pendientes(self) -> None:
        with self.assertRaises(DatosNormativosPendientesError):
            crear_configuracion_uc_inicial()

    def test_construye_agregado_cuando_los_datos_estan_completos(
        self,
    ) -> None:
        rangos = self._crear_rangos()

        with patch.multiple(
            "app.initial_data.configuracion_uc_inicial",
            FECHA_INICIO_VIGENCIA=date(2026, 1, 1),
            VALOR_UC=Decimal("1000"),
            MONEDA="MONEDA_CONFIRMADA",
            RESOLUCION="RESOLUCION_CONFIRMADA",
            ORGANISMO_EMISOR="ORGANISMO_CONFIRMADO",
            RANGOS=rangos,
        ):
            configuracion = crear_configuracion_uc_inicial()

        self.assertEqual(
            configuracion.id_configuracion,
            CONFIGURACION_UC_INICIAL_ID,
        )
        self.assertEqual(configuracion.rangos, rangos)
        self.assertEqual(configuracion.estado, "VIGENTE")
        self.assertIsNone(configuracion.fecha_fin_vigencia)

    def test_comparacion_considera_el_agregado_completo(self) -> None:
        original = self._crear_configuracion(Decimal("1000"))
        divergente = self._crear_configuracion(Decimal("1001"))
        repository = RepositorioConfiguracionUCFalso(original)
        registrar = RegistrarConfiguracionUC(repository)
        estrategia = EstrategiaCargaInicialConfiguracionUC(
            repository,
            registrar,
        )

        with self.assertRaises(CargaInicialDivergenteError):
            ejecutar_carga_inicial(
                nombre_carga="Configuración UC inicial",
                dato=divergente,
                estrategia=estrategia,
            )

        self.assertEqual(repository.existente, original)
        self.assertEqual(repository.guardados, [])

    def test_estrategia_delega_el_guardado_en_el_caso_de_uso(
        self,
    ) -> None:
        repository = RepositorioConfiguracionUCFalso()
        registrar = RegistrarConfiguracionUC(repository)
        estrategia = EstrategiaCargaInicialConfiguracionUC(
            repository,
            registrar,
        )
        configuracion = self._crear_configuracion(Decimal("1000"))

        estrategia.guardar(configuracion)

        self.assertEqual(repository.guardados, [configuracion])

    def test_carga_identica_no_intenta_registrar_nuevamente(
        self,
    ) -> None:
        configuracion = self._crear_configuracion(Decimal("1000"))
        repository = RepositorioConfiguracionUCFalso(configuracion)
        registrar = RegistrarConfiguracionUC(repository)
        estrategia = EstrategiaCargaInicialConfiguracionUC(
            repository,
            registrar,
        )

        resultado = ejecutar_carga_inicial(
            nombre_carga="Configuración UC inicial",
            dato=configuracion,
            estrategia=estrategia,
        )

        self.assertEqual(
            resultado,
            ResultadoCargaInicial.YA_EXISTENTE,
        )
        self.assertEqual(repository.guardados, [])

    @classmethod
    def _crear_configuracion(
        cls,
        valor_uc: Decimal,
    ) -> ConfiguracionUC:
        return ConfiguracionUC(
            id_configuracion=CONFIGURACION_UC_INICIAL_ID,
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=valor_uc,
            moneda="MONEDA_DE_PRUEBA",
            resolucion="RESOLUCION_DE_PRUEBA",
            organismo_emisor="ORGANISMO_DE_PRUEBA",
            estado="ESTADO_DE_PRUEBA",
            rangos=cls._crear_rangos(),
        )

    @staticmethod
    def _crear_rangos() -> tuple[RangoProcedimientoUC, ...]:
        configuracion_id = CONFIGURACION_UC_INICIAL_ID
        return (
            RangoProcedimientoUC(
                id_rango="rango-prueba-1",
                configuracion_uc_id=configuracion_id,
                limite_inferior=Decimal("0"),
                limite_superior=Decimal("100"),
                limite_inferior_inclusivo=True,
                limite_superior_inclusivo=True,
                procedimiento="PROCEDIMIENTO_DE_PRUEBA_1",
                articulo="ARTICULO_DE_PRUEBA",
                inciso="INCISO_DE_PRUEBA",
                referencia_normativa="REFERENCIA_DE_PRUEBA",
            ),
            RangoProcedimientoUC(
                id_rango="rango-prueba-2",
                configuracion_uc_id=configuracion_id,
                limite_inferior=Decimal("100"),
                limite_superior=Decimal("200"),
                limite_inferior_inclusivo=False,
                limite_superior_inclusivo=True,
                procedimiento="PROCEDIMIENTO_DE_PRUEBA_2",
                articulo="ARTICULO_DE_PRUEBA",
                inciso="INCISO_DE_PRUEBA",
                referencia_normativa="REFERENCIA_DE_PRUEBA",
            ),
        )


if __name__ == "__main__":
    unittest.main()
