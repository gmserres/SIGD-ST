import unittest
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.expedientes import (
    _analizar_op_o_conflicto,
    analizar_op,
    obtener_analisis_op,
)
from app.application.configuracion_uc.determinar_procedimiento_contratacion import (
    ResultadoDeterminacionProcedimiento,
)
from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ConfiguracionUCVigenteNoEncontradaError,
)
from app.domain.configuracion_uc import ConfiguracionUC, RangoProcedimientoUC
from app.modules.documentos.extractor_datos import DatosOPExtraidos
from app.services.analisis_op import (
    AnalisisOPService,
    ConfiguracionUCNoAsociadaError,
    ConfiguracionUCHistoricaNoEncontradaError,
)


class MotorFalso:
    def __init__(
        self,
        resultado: ResultadoDeterminacionProcedimiento,
    ) -> None:
        self.resultado = resultado
        self.vigentes: list[tuple[date, Decimal]] = []
        self.historicas: list[tuple[ConfiguracionUC, Decimal]] = []

    def ejecutar(
        self,
        fecha: date,
        monto: Decimal,
    ) -> ResultadoDeterminacionProcedimiento:
        self.vigentes.append((fecha, monto))
        return self.resultado

    def ejecutar_con_configuracion(
        self,
        configuracion: ConfiguracionUC,
        monto: Decimal,
    ) -> ResultadoDeterminacionProcedimiento:
        self.historicas.append((configuracion, monto))
        return ResultadoDeterminacionProcedimiento(
            monto=monto,
            cantidad_uc=monto / configuracion.valor_uc,
            valor_uc=configuracion.valor_uc,
            configuracion=configuracion,
            rango=configuracion.rangos[0],
        )


class AsociacionConfiguracionUCExpedienteTest(unittest.TestCase):
    def test_api_traduce_configuracion_vigente_inexistente(self) -> None:
        error = ConfiguracionUCVigenteNoEncontradaError(
            date(2026, 7, 29)
        )

        with patch(
            "app.api.expedientes.analisis_op_service.analizar",
            side_effect=error,
        ):
            with self.assertRaises(HTTPException) as contexto:
                _analizar_op_o_conflicto("EXP-1")

        self.assertEqual(contexto.exception.status_code, 409)
        self.assertEqual(
            contexto.exception.detail,
            {
                "mensaje": str(error),
                "errores": [
                    "No existe una Configuración UC vigente para analizar "
                    "la Orden de Pago."
                ],
            },
        )
        self.assertIs(contexto.exception.__cause__, error)

    def test_api_mantiene_traduccion_configuracion_historica(self) -> None:
        error = ConfiguracionUCHistoricaNoEncontradaError(
            "configuracion-inexistente"
        )

        with patch(
            "app.api.expedientes.analisis_op_service.analizar",
            side_effect=error,
        ):
            with self.assertRaises(HTTPException) as contexto:
                _analizar_op_o_conflicto("EXP-1")

        self.assertEqual(contexto.exception.status_code, 409)
        self.assertEqual(contexto.exception.detail["mensaje"], str(error))
        self.assertEqual(
            contexto.exception.detail["errores"],
            [
                "La referencia histórica de Configuración UC "
                "no pudo ser recuperada."
            ],
        )
        self.assertIs(contexto.exception.__cause__, error)

    def test_primer_analisis_asocia_mediante_servicio_especifico(
        self,
    ) -> None:
        motor = MotorFalso(self._resultado("configuracion-1"))

        with self._parches(self._expediente(None)) as asociar:
            AnalisisOPService(motor, MagicMock()).analizar("EXP-1")

        asociar.assert_called_once_with("EXP-1", "configuracion-1")

    def test_segundo_analisis_reutiliza_configuracion_sin_asociar(
        self,
    ) -> None:
        configuracion = self._configuracion("configuracion-1")
        motor = MotorFalso(self._resultado("configuracion-reciente"))
        repositorio = MagicMock()
        repositorio.obtener_por_id.return_value = configuracion

        with self._parches(
            self._expediente("configuracion-1")
        ) as asociar:
            analisis = AnalisisOPService(
                motor,
                repositorio,
            ).analizar("EXP-1")

        repositorio.obtener_por_id.assert_called_once_with(
            "configuracion-1"
        )
        self.assertEqual(motor.vigentes, [])
        self.assertEqual(
            motor.historicas,
            [(configuracion, Decimal("12000.0"))],
        )
        self.assertEqual(analisis.valor_uc, Decimal("1000"))
        asociar.assert_not_called()

    def test_configuracion_historica_prevalece_sobre_una_mas_reciente(
        self,
    ) -> None:
        historica = self._configuracion(
            "configuracion-historica",
            valor_uc=Decimal("1000"),
        )
        motor = MotorFalso(
            self._resultado(
                "configuracion-reciente",
                valor_uc=Decimal("2000"),
            )
        )
        repositorio = MagicMock()
        repositorio.obtener_por_id.return_value = historica

        with self._parches(
            self._expediente("configuracion-historica")
        ) as asociar:
            analisis = AnalisisOPService(
                motor,
                repositorio,
            ).analizar("EXP-1")

        self.assertEqual(motor.vigentes, [])
        self.assertEqual(analisis.valor_uc, Decimal("1000"))
        asociar.assert_not_called()

    def test_referencia_inexistente_no_usa_alternativa_ni_modifica(
        self,
    ) -> None:
        motor = MotorFalso(self._resultado("configuracion-reciente"))
        repositorio = MagicMock()
        repositorio.obtener_por_id.return_value = None

        with self._parches(
            self._expediente("configuracion-inexistente")
        ) as asociar:
            with self.assertRaises(
                ConfiguracionUCHistoricaNoEncontradaError
            ):
                AnalisisOPService(
                    motor,
                    repositorio,
                ).analizar("EXP-1")

        self.assertEqual(motor.vigentes, [])
        self.assertEqual(motor.historicas, [])
        asociar.assert_not_called()

    def test_dos_reconstrucciones_reutilizan_configuracion_sin_asociar(
        self,
    ) -> None:
        configuracion = self._configuracion("configuracion-1")
        motor = MotorFalso(self._resultado("configuracion-reciente"))
        repositorio = MagicMock()
        repositorio.obtener_por_id.return_value = configuracion
        servicio = AnalisisOPService(motor, repositorio)

        with self._parches(
            self._expediente("configuracion-1")
        ) as asociar:
            primero = servicio.reconstruir("EXP-1")
            segundo = servicio.reconstruir("EXP-1")

        self.assertEqual(primero, segundo)
        self.assertEqual(len(motor.historicas), 2)
        asociar.assert_not_called()

    def test_reconstruccion_sin_configuracion_no_asocia(self) -> None:
        motor = MotorFalso(self._resultado("configuracion-1"))

        with self._parches(self._expediente(None)) as asociar:
            with self.assertRaises(ConfiguracionUCNoAsociadaError):
                AnalisisOPService(motor, MagicMock()).reconstruir("EXP-1")

        self.assertEqual(motor.vigentes, [])
        asociar.assert_not_called()

    def test_get_reconstruye_sin_registrar_historial(self) -> None:
        esperado = SimpleNamespace(modo="ALFA_PDF_TEXTO")

        with patch(
            "app.api.expedientes.obtener_expediente"
        ), patch(
            "app.api.expedientes.analisis_op_service.reconstruir",
            return_value=esperado,
        ) as reconstruir, patch(
            "app.api.expedientes.historial_service.registrar"
        ) as registrar:
            resultado = obtener_analisis_op("EXP-1")

        self.assertIs(resultado, esperado)
        reconstruir.assert_called_once_with("EXP-1")
        registrar.assert_not_called()

    def test_get_traduce_configuracion_no_asociada_sin_corregirla(self) -> None:
        error = ConfiguracionUCNoAsociadaError("EXP-1")

        with patch(
            "app.services.analisis_op.expediente_service.asociar_configuracion_uc"
        ) as asociar, patch(
            "app.api.expedientes.analisis_op_service.reconstruir",
            side_effect=error,
        ):
            with self.assertRaises(HTTPException) as contexto:
                _analizar_op_o_conflicto("EXP-1", reconstruir=True)

        self.assertEqual(contexto.exception.status_code, 409)
        asociar.assert_not_called()

    def test_post_conserva_analisis_e_historial(self) -> None:
        analisis = SimpleNamespace(modo="ALFA_PDF_TEXTO")

        with patch(
            "app.api.expedientes.obtener_expediente"
        ), patch(
            "app.api.expedientes.validacion_service.tiene_op",
            return_value=True,
        ), patch(
            "app.api.expedientes.analisis_op_service.analizar",
            return_value=analisis,
        ) as ejecutar, patch(
            "app.api.expedientes.historial_service.registrar"
        ) as registrar:
            resultado = analizar_op("EXP-1")

        self.assertIs(resultado, analisis)
        ejecutar.assert_called_once_with("EXP-1")
        registrar.assert_called_once_with(
            "EXP-1", "OP_ANALIZADA_IA", detalle="Modo ALFA_PDF_TEXTO"
        )

    @contextmanager
    def _parches(self, expediente):
        datos = DatosOPExtraidos(
            texto_extraido="ORDEN DE PAGO",
            paginas=1,
            cuit="30-00000000-0",
            fecha="10/07/2026",
            orden_pago="OP 1",
            liquidacion="2026-1",
            proveedor="PROVEEDOR",
            fondo="Fondo Compensador",
            monto_total_facturas=12000.0,
            monto_neto_pagar=11000.0,
            importe_pago=None,
            importe_probable=None,
            importe_contexto="Monto Total",
            facturas=[],
            retenciones=[],
            advertencias=[],
        )
        documento = SimpleNamespace(tipo="OP", ruta="op.pdf")
        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=expediente,
        ), patch(
            "app.services.analisis_op."
            "expediente_service.asociar_configuracion_uc"
        ) as asociar, patch(
            "app.services.analisis_op."
            "documento_service.listar_por_expediente",
            return_value=[documento],
        ), patch(
            "app.services.analisis_op.extraer_datos_op_desde_pdf",
            return_value=datos,
        ), patch(
            "app.services.analisis_op.checklist_fisico_service.obtener",
            return_value=None,
        ):
            yield asociar

    @staticmethod
    def _expediente(configuracion_uc_id: str | None):
        return SimpleNamespace(
            creado=datetime(2026, 7, 10, 15, 30),
            configuracion_uc_id=configuracion_uc_id,
        )

    def _resultado(
        self,
        configuracion_id: str,
        valor_uc: Decimal = Decimal("1000"),
    ) -> ResultadoDeterminacionProcedimiento:
        configuracion = self._configuracion(
            configuracion_id,
            valor_uc,
        )
        return ResultadoDeterminacionProcedimiento(
            monto=Decimal("12000"),
            cantidad_uc=Decimal("12000") / valor_uc,
            valor_uc=valor_uc,
            configuracion=configuracion,
            rango=configuracion.rangos[0],
        )

    @staticmethod
    def _configuracion(
        configuracion_id: str,
        valor_uc: Decimal = Decimal("1000"),
    ) -> ConfiguracionUC:
        rango = RangoProcedimientoUC(
            id_rango=f"rango-{configuracion_id}",
            configuracion_uc_id=configuracion_id,
            limite_inferior=Decimal("0"),
            limite_superior=Decimal("1000000"),
            limite_inferior_inclusivo=True,
            limite_superior_inclusivo=True,
            procedimiento="PROCEDIMIENTO",
            articulo="ARTICULO",
            inciso="INCISO",
            referencia_normativa="REFERENCIA",
        )
        return ConfiguracionUC(
            id_configuracion=configuracion_id,
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=valor_uc,
            moneda="ARS",
            resolucion="RESOLUCION",
            organismo_emisor="ORGANISMO",
            estado="ACTIVA",
            rangos=(rango,),
        )


if __name__ == "__main__":
    unittest.main()
