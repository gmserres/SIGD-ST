import json
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.application.configuracion_uc.determinar_procedimiento_contratacion import (
    MultiplesRangosProcedimientoUCError,
    RangoProcedimientoUCNoEncontradoError,
    ResultadoDeterminacionProcedimiento,
)
from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ConfiguracionUCVigenteNoEncontradaError,
    SuperposicionConfiguracionesUCError,
)
from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)
from app.modules.documentos.extractor_datos import DatosOPExtraidos, FacturaExtraida
from app.schemas.checklist_fisico import ChecklistFisicoRead
from app.services.analisis_op import AnalisisOPService
from app.services.disposiciones import DisposicionService


class MotorDeterminacionFalso:
    def __init__(
        self,
        resultado: ResultadoDeterminacionProcedimiento,
    ) -> None:
        self.resultado = resultado
        self.invocaciones: list[tuple[date, Decimal]] = []
        self.invocaciones_historicas: list[
            tuple[ConfiguracionUC, Decimal]
        ] = []
        self.error: Exception | None = None

    def ejecutar(
        self,
        fecha: date,
        monto: Decimal,
    ) -> ResultadoDeterminacionProcedimiento:
        self.invocaciones.append((fecha, monto))
        if self.error is not None:
            raise self.error
        return self.resultado

    def ejecutar_con_configuracion(
        self,
        configuracion: ConfiguracionUC,
        monto: Decimal,
    ) -> ResultadoDeterminacionProcedimiento:
        self.invocaciones_historicas.append((configuracion, monto))
        if self.error is not None:
            raise self.error
        return self.resultado


class IntegracionMotorUCFondoCompensadorTest(unittest.TestCase):
    def test_analisis_delega_fecha_monto_y_conserva_resultado(
        self,
    ) -> None:
        motor = MotorDeterminacionFalso(self._crear_resultado())
        servicio = AnalisisOPService(motor, MagicMock())

        analisis = self._analizar(
            servicio,
            monto_total_facturas=12345.67,
            importe_pago=12000.0,
            importe_probable=11000.0,
        )

        self.assertEqual(
            motor.invocaciones,
            [(date(2026, 7, 10), Decimal("12345.67"))],
        )
        self.assertEqual(analisis.cantidad_uc, Decimal("12.34567"))
        self.assertEqual(analisis.valor_uc, Decimal("1000"))
        self.assertEqual(analisis.procedimiento, "PROCEDIMIENTO_CONFIGURADO")
        self.assertEqual(analisis.articulo, "ARTICULO_CONFIGURADO")
        self.assertEqual(analisis.inciso, "INCISO_CONFIGURADO")
        self.assertEqual(analisis.norma_uc, "REFERENCIA_CONFIGURADA")
        self.assertEqual(
            analisis.encuadre_legal,
            "ARTICULO_CONFIGURADO INCISO_CONFIGURADO. "
            "REFERENCIA_CONFIGURADA",
        )

    def test_respeta_prioridad_actual_de_importes(self) -> None:
        casos = (
            (100.25, 90.5, 80.75, Decimal("100.25")),
            (None, 90.5, 80.75, Decimal("90.5")),
            (None, None, 80.75, Decimal("80.75")),
        )

        for monto_total, importe_pago, probable, esperado in casos:
            with self.subTest(esperado=esperado):
                motor = MotorDeterminacionFalso(self._crear_resultado())
                servicio = AnalisisOPService(motor, MagicMock())

                self._analizar(
                    servicio,
                    monto_total_facturas=monto_total,
                    importe_pago=importe_pago,
                    importe_probable=probable,
                )

                self.assertEqual(motor.invocaciones[0][1], esperado)

    def test_op_ausente_no_devuelve_parametros_uc_heredados(
        self,
    ) -> None:
        motor = MotorDeterminacionFalso(self._crear_resultado())
        servicio = AnalisisOPService(motor, MagicMock())

        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=self._expediente(),
        ), patch(
            "app.services.analisis_op.documento_service.listar_por_expediente",
            return_value=[],
        ):
            analisis = servicio.analizar("EXP-1")

        self.assertEqual(motor.invocaciones, [])
        self.assertIsNone(analisis.valor_uc)
        self.assertIsNone(analisis.norma_uc)
        self.assertIsNone(analisis.cantidad_uc)
        self.assertIsNone(analisis.procedimiento)
        self.assertIsNone(analisis.articulo)
        self.assertIsNone(analisis.inciso)

    def test_propaga_excepciones_del_motor(self) -> None:
        fecha = date(2026, 7, 10)
        errores = (
            ConfiguracionUCVigenteNoEncontradaError(fecha),
            SuperposicionConfiguracionesUCError(
                fecha,
                ("configuracion-1", "configuracion-2"),
            ),
            RangoProcedimientoUCNoEncontradoError(
                Decimal("12.5"),
                "configuracion-1",
            ),
            MultiplesRangosProcedimientoUCError(
                Decimal("12.5"),
                "configuracion-1",
                ("rango-1", "rango-2"),
            ),
        )

        for error in errores:
            with self.subTest(error=type(error).__name__):
                motor = MotorDeterminacionFalso(self._crear_resultado())
                motor.error = error
                servicio = AnalisisOPService(motor, MagicMock())

                with self.assertRaises(type(error)) as contexto:
                    self._analizar(servicio)

                self.assertIs(contexto.exception, error)

    def test_contrato_json_serializa_decimales_y_nuevos_campos(
        self,
    ) -> None:
        analisis = self._analizar(
            AnalisisOPService(
                MotorDeterminacionFalso(self._crear_resultado()),
                MagicMock(),
            )
        )

        contenido = json.loads(analisis.model_dump_json())

        self.assertEqual(contenido["cantidad_uc"], "12.34567")
        self.assertEqual(contenido["valor_uc"], "1000")
        self.assertEqual(contenido["articulo"], "ARTICULO_CONFIGURADO")
        self.assertEqual(contenido["inciso"], "INCISO_CONFIGURADO")

    def test_disposicion_consume_resultado_sin_recalcular_uc(
        self,
    ) -> None:
        servicio = DisposicionService()
        analisis = SimpleNamespace(
            importe_bruto=999999.0,
            fecha_op="10/07/2026",
            documentos_comerciales=[],
            retenciones=[],
            importe_neto=900000.0,
            fondo="Fondo Compensador",
            proveedor="PROVEEDOR",
            cuit="30-00000000-0",
            cantidad_uc=Decimal("12.34567"),
            valor_uc=Decimal("1000"),
            norma_uc="REFERENCIA_CONFIGURADA",
            procedimiento="PROCEDIMIENTO_CONFIGURADO",
            articulo="ARTICULO_CONFIGURADO",
            inciso="INCISO_CONFIGURADO",
        )
        expediente = SimpleNamespace(
            id_suna="123",
            numero_interno="033-1/2026",
            numero_disposicion=None,
            objeto="OBJETO",
            establecimiento="ESTABLECIMIENTO",
        )

        variables = servicio._construir_variables(
            expediente,
            analisis,
            None,
        )

        self.assertEqual(variables["UC"], "12,35")
        self.assertEqual(variables["NORMA_UC"], "REFERENCIA_CONFIGURADA")
        self.assertEqual(
            variables["ARTICULO_DR"],
            "ARTICULO_CONFIGURADO INCISO_CONFIGURADO",
        )
        self.assertEqual(
            variables["PROCEDIMIENTO"],
            "PROCEDIMIENTO_CONFIGURADO",
        )
        self.assertEqual(variables["EJERCICIO"], str(date.today().year))

    def test_analisis_no_referencia_reglas_uc_heredadas(self) -> None:
        fuente = Path(
            "app/services/analisis_op.py"
        ).read_text(encoding="utf-8")

        for nombre in (
            "VALOR_UC_VIGENTE",
            "NORMA_UC",
            "calcular_uc",
            "determinar_procedimiento(",
            "encuadre_legal(",
        ):
            self.assertNotIn(nombre, fuente)

    def test_checklist_completo_elimina_faltantes_documentales(self) -> None:
        analisis = self._analizar(
            AnalisisOPService(
                MotorDeterminacionFalso(self._crear_resultado()),
                MagicMock(),
            ),
            checklist=self._checklist(True, True, True, True, True),
        )

        self.assertEqual(analisis.faltantes, [])
        self.assertTrue(
            any(
                validacion.startswith("Confiabilidad documental: ")
                for validacion in analisis.validaciones
            )
        )
        self.assertTrue(
            any(
                validacion.startswith("Riesgo administrativo: ")
                for validacion in analisis.validaciones
            )
        )

    def test_factura_extraida_de_op_no_figura_como_faltante(self) -> None:
        factura = FacturaExtraida(
            tipo="Factura",
            letra="A",
            numero="00001-00000005",
            fecha="10/07/2026",
            importe=12345.67,
        )

        analisis = self._analizar(
            AnalisisOPService(
                MotorDeterminacionFalso(self._crear_resultado()),
                MagicMock(),
            ),
            facturas=[factura],
        )

        self.assertNotIn("Factura", analisis.faltantes)

    def test_checklist_parcial_conserva_solo_faltantes_reales(self) -> None:
        analisis = self._analizar(
            AnalisisOPService(
                MotorDeterminacionFalso(self._crear_resultado()),
                MagicMock(),
            ),
            checklist=self._checklist(True, True, False, True, False),
        )

        self.assertEqual(
            analisis.faltantes,
            ["Validación CAE", "Certificado Fiscal ARBA"],
        )

    def test_sin_evidencias_conserva_cinco_faltantes_documentales(self) -> None:
        analisis = self._analizar(
            AnalisisOPService(
                MotorDeterminacionFalso(self._crear_resultado()),
                MagicMock(),
            )
        )

        self.assertEqual(
            analisis.faltantes,
            [
                "Factura",
                "Remito o conformidad firmada",
                "Validación CAE",
                "Certificado Fiscal ARBA",
                "Constancia ARCA",
            ],
        )
        self.assertEqual(analisis.cantidad_uc, Decimal("12.34567"))
        self.assertEqual(analisis.procedimiento, "PROCEDIMIENTO_CONFIGURADO")
        self.assertEqual(analisis.norma_uc, "REFERENCIA_CONFIGURADA")

    def _analizar(
        self,
        servicio: AnalisisOPService,
        monto_total_facturas: float | None = 12345.67,
        importe_pago: float | None = None,
        importe_probable: float | None = None,
        facturas: list[FacturaExtraida] | None = None,
        checklist: ChecklistFisicoRead | None = None,
    ):
        datos = DatosOPExtraidos(
            texto_extraido="ORDEN DE PAGO",
            paginas=1,
            cuit="30-00000000-0",
            fecha="10/07/2026",
            orden_pago="OP 1",
            liquidacion="2026-1",
            proveedor="PROVEEDOR",
            fondo="Fondo Compensador",
            monto_total_facturas=monto_total_facturas,
            monto_neto_pagar=12000.0,
            importe_pago=importe_pago,
            importe_probable=importe_probable,
            importe_contexto="Monto Total",
            facturas=facturas or [],
            retenciones=[],
            advertencias=[],
        )
        documento = SimpleNamespace(tipo="OP", ruta="op.pdf")

        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=self._expediente(),
        ), patch(
            "app.services.analisis_op.documento_service.listar_por_expediente",
            return_value=[documento],
        ), patch(
            "app.services.analisis_op.extraer_datos_op_desde_pdf",
            return_value=datos,
        ), patch(
            "app.services.analisis_op.checklist_fisico_service.obtener",
            return_value=checklist,
        ), patch(
            "app.services.analisis_op."
            "expediente_service.asociar_configuracion_uc",
        ):
            return servicio.analizar("EXP-1")

    @staticmethod
    def _checklist(
        factura: bool,
        remito: bool,
        cae: bool,
        arca: bool,
        arba: bool,
    ) -> ChecklistFisicoRead:
        return ChecklistFisicoRead(
            expediente_id="EXP-1",
            factura=factura,
            remito_conformidad=remito,
            cae=cae,
            arca=arca,
            arba=arba,
            usuario="Operador",
            fecha=datetime(2026, 8, 5),
        )

    @staticmethod
    def _expediente():
        return SimpleNamespace(
            creado=datetime(2026, 7, 10, 15, 30),
            configuracion_uc_id=None,
        )

    @staticmethod
    def _crear_resultado() -> ResultadoDeterminacionProcedimiento:
        rango = RangoProcedimientoUC(
            id_rango="rango-1",
            configuracion_uc_id="configuracion-1",
            limite_inferior=Decimal("0"),
            limite_superior=Decimal("100"),
            limite_inferior_inclusivo=True,
            limite_superior_inclusivo=True,
            procedimiento="PROCEDIMIENTO_CONFIGURADO",
            articulo="ARTICULO_CONFIGURADO",
            inciso="INCISO_CONFIGURADO",
            referencia_normativa="REFERENCIA_CONFIGURADA",
        )
        configuracion = ConfiguracionUC(
            id_configuracion="configuracion-1",
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=Decimal("1000"),
            moneda="MONEDA_DE_PRUEBA",
            resolucion="RESOLUCION_DE_PRUEBA",
            organismo_emisor="ORGANISMO_DE_PRUEBA",
            estado="ACTIVA",
            rangos=(rango,),
        )
        return ResultadoDeterminacionProcedimiento(
            monto=Decimal("12345.67"),
            cantidad_uc=Decimal("12.34567"),
            valor_uc=Decimal("1000"),
            configuracion=configuracion,
            rango=rango,
        )


if __name__ == "__main__":
    unittest.main()
