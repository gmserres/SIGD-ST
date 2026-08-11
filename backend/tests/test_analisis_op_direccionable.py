import unittest
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.expedientes import (
    _analizar_documento_op_o_error,
    analizar_documento_op,
    obtener_analisis_documento_op,
)
from app.application.configuracion_uc.determinar_procedimiento_contratacion import (
    ResultadoDeterminacionProcedimiento,
)
from app.domain.configuracion_uc import ConfiguracionUC, RangoProcedimientoUC
from app.modules.documentos.extractor_datos import DatosOPExtraidos
from app.services.analisis_op import (
    AnalisisOPService,
    ArchivoOPNoAnalizableError,
    ArchivoOPNoDisponibleError,
    ConfiguracionUCNoAsociadaError,
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)


class MotorFalso:
    def __init__(self, resultado):
        self.resultado = resultado
        self.vigentes = []
        self.historicas = []

    def ejecutar(self, fecha, monto):
        self.vigentes.append((fecha, monto))
        return self.resultado

    def ejecutar_con_configuracion(self, configuracion, monto):
        self.historicas.append((configuracion, monto))
        return self.resultado


class AnalisisOPDireccionableTest(unittest.TestCase):
    def setUp(self) -> None:
        self.resultado = self._resultado()
        self.motor = MotorFalso(self.resultado)
        self.configuraciones = MagicMock()
        self.servicio = AnalisisOPService(
            self.motor,
            self.configuraciones,
        )
        self.expediente = self._expediente(None)
        self.op_a = self._documento(
            "DOC-000001", "EXP-1", "OP", "op-a.pdf"
        )
        self.op_b = self._documento(
            "DOC-000002", "EXP-1", "OP", "op-b.pdf"
        )

    def test_analiza_op_a_sin_depender_del_orden(self) -> None:
        with self._parches([self.op_b, self.op_a]):
            analisis = self.servicio.analizar_documento(
                "EXP-1", self.op_a.id
            )

        self.assertEqual(analisis.documento_op_id, self.op_a.id)
        self.assertEqual(analisis.orden_pago, "OP A")
        self.assertEqual(analisis.cuit, "30-00000000-1")

    def test_analiza_op_b_sin_depender_del_orden(self) -> None:
        with self._parches([self.op_a, self.op_b]):
            analisis = self.servicio.analizar_documento(
                "EXP-1", self.op_b.id
            )

        self.assertEqual(analisis.documento_op_id, self.op_b.id)
        self.assertEqual(analisis.orden_pago, "OP B")
        self.assertEqual(analisis.cuit, "30-00000000-2")

    def test_documento_inexistente(self) -> None:
        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=self.expediente,
        ), patch(
            "app.services.analisis_op.documento_service.obtener_por_id",
            return_value=None,
        ):
            with self.assertRaises(DocumentoOPNoEncontradoError):
                self.servicio.analizar_documento(
                    "EXP-1", "DOC-999999"
                )

    def test_documento_de_otro_expediente(self) -> None:
        documento = self._documento(
            "DOC-000003", "EXP-2", "OP", "op.pdf"
        )
        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=self.expediente,
        ), patch(
            "app.services.analisis_op.documento_service.obtener_por_id",
            return_value=documento,
        ):
            with self.assertRaises(
                DocumentoOPExpedienteInconsistenteError
            ):
                self.servicio.analizar_documento(
                    "EXP-1", documento.id
                )

    def test_documento_que_no_es_op(self) -> None:
        documento = self._documento(
            "DOC-000003", "EXP-1", "FACTURA", "factura.pdf"
        )
        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=self.expediente,
        ), patch(
            "app.services.analisis_op.documento_service.obtener_por_id",
            return_value=documento,
        ):
            with self.assertRaises(DocumentoNoEsOPError):
                self.servicio.analizar_documento(
                    "EXP-1", documento.id
                )

    def test_archivo_fisico_inexistente(self) -> None:
        with self._parches([self.op_a], archivo_disponible=False):
            with self.assertRaises(ArchivoOPNoDisponibleError):
                self.servicio.analizar_documento(
                    "EXP-1", self.op_a.id
                )

    def test_archivo_presente_pero_no_analizable(self) -> None:
        with self._parches([self.op_a], texto_extraido=""):
            with self.assertRaises(ArchivoOPNoAnalizableError):
                self.servicio.analizar_documento(
                    "EXP-1", self.op_a.id
                )

    def test_primera_op_direccionada_asocia_configuracion(self) -> None:
        with self._parches([self.op_a]) as asociar:
            self.servicio.analizar_documento("EXP-1", self.op_a.id)

        asociar.assert_called_once_with(
            "EXP-1", self.resultado.configuracion.id_configuracion
        )

    def test_segunda_op_reutiliza_configuracion_sin_reasociar(self) -> None:
        self.expediente = self._expediente(
            self.resultado.configuracion.id_configuracion
        )
        self.configuraciones.obtener_por_id.return_value = (
            self.resultado.configuracion
        )

        with self._parches([self.op_a, self.op_b]) as asociar:
            analisis = self.servicio.analizar_documento(
                "EXP-1", self.op_b.id
            )

        self.configuraciones.obtener_por_id.assert_called_once_with(
            self.resultado.configuracion.id_configuracion
        )
        self.assertEqual(len(self.motor.historicas), 1)
        self.assertEqual(analisis.documento_op_id, self.op_b.id)
        asociar.assert_not_called()

    def test_reconstruccion_direccionada_no_asocia(self) -> None:
        self.expediente = self._expediente(
            self.resultado.configuracion.id_configuracion
        )
        self.configuraciones.obtener_por_id.return_value = (
            self.resultado.configuracion
        )

        with self._parches([self.op_a]) as asociar:
            self.servicio.reconstruir_documento(
                "EXP-1", self.op_a.id
            )

        asociar.assert_not_called()

    def test_reconstruccion_sin_configuracion_no_asocia(self) -> None:
        with self._parches([self.op_a]) as asociar:
            with self.assertRaises(ConfiguracionUCNoAsociadaError):
                self.servicio.reconstruir_documento(
                    "EXP-1", self.op_a.id
                )

        asociar.assert_not_called()

    def test_post_direccionado_registra_documento(self) -> None:
        esperado = SimpleNamespace(modo="ALFA_PDF_TEXTO")
        with patch(
            "app.api.expedientes.obtener_expediente"
        ), patch(
            "app.api.expedientes.analisis_op_service.analizar_documento",
            return_value=esperado,
        ) as analizar, patch(
            "app.api.expedientes.historial_service.registrar"
        ) as registrar:
            resultado = analizar_documento_op(
                "EXP-1", "DOC-000001"
            )

        self.assertIs(resultado, esperado)
        analizar.assert_called_once_with("EXP-1", "DOC-000001")
        registrar.assert_called_once_with(
            "EXP-1",
            "OP_ANALIZADA_IA",
            detalle="Documento DOC-000001 | Modo ALFA_PDF_TEXTO",
        )

    def test_get_direccionado_no_registra_historial(self) -> None:
        esperado = SimpleNamespace(modo="ALFA_PDF_TEXTO")
        with patch(
            "app.api.expedientes.obtener_expediente"
        ), patch(
            "app.api.expedientes.analisis_op_service.reconstruir_documento",
            return_value=esperado,
        ) as reconstruir, patch(
            "app.api.expedientes.historial_service.registrar"
        ) as registrar:
            resultado = obtener_analisis_documento_op(
                "EXP-1", "DOC-000001"
            )

        self.assertIs(resultado, esperado)
        reconstruir.assert_called_once_with("EXP-1", "DOC-000001")
        registrar.assert_not_called()

    def test_api_traduce_documento_inexistente_a_404(self) -> None:
        self._comprobar_http(
            DocumentoOPNoEncontradoError("DOC-999999"), 404
        )

    def test_api_traduce_documento_inconsistente_a_409(self) -> None:
        self._comprobar_http(
            DocumentoOPExpedienteInconsistenteError(
                "DOC-000001", "EXP-1"
            ),
            409,
        )

    def test_api_traduce_documento_no_op_a_422(self) -> None:
        self._comprobar_http(
            DocumentoNoEsOPError("DOC-000001"), 422
        )

    def test_api_traduce_archivo_inexistente_a_409(self) -> None:
        self._comprobar_http(
            ArchivoOPNoDisponibleError("DOC-000001"), 409
        )

    def test_api_traduce_archivo_no_analizable_a_422(self) -> None:
        self._comprobar_http(
            ArchivoOPNoAnalizableError("DOC-000001"), 422
        )

    def _comprobar_http(self, error, estado) -> None:
        with patch(
            "app.api.expedientes.analisis_op_service.analizar_documento",
            side_effect=error,
        ):
            with self.assertRaises(HTTPException) as contexto:
                _analizar_documento_op_o_error(
                    "EXP-1", "DOC-000001"
                )

        self.assertEqual(contexto.exception.status_code, estado)

    @contextmanager
    def _parches(
        self,
        documentos,
        *,
        archivo_disponible=True,
        texto_extraido=None,
    ):
        def extraer(ruta):
            orden = "OP A" if ruta.name == "op-a.pdf" else "OP B"
            cuit = (
                "30-00000000-1"
                if ruta.name == "op-a.pdf"
                else "30-00000000-2"
            )
            texto = orden if texto_extraido is None else texto_extraido
            return self._datos(texto, orden, cuit)

        def obtener(documento_id):
            return next(
                documento
                for documento in documentos
                if documento.id == documento_id
            )

        with patch(
            "app.services.analisis_op.expediente_service.obtener",
            return_value=self.expediente,
        ), patch(
            "app.services.analisis_op.documento_service.obtener_por_id",
            side_effect=obtener,
        ), patch(
            "app.services.analisis_op.documento_service.listar_por_expediente",
            return_value=documentos,
        ), patch(
            "app.services.analisis_op.checklist_fisico_service.obtener",
            return_value=None,
        ), patch(
            "app.services.analisis_op.Path.is_file",
            return_value=archivo_disponible,
        ), patch(
            "app.services.analisis_op.extraer_datos_op_desde_pdf",
            side_effect=extraer,
        ), patch(
            "app.services.analisis_op.expediente_service.asociar_configuracion_uc"
        ) as asociar:
            yield asociar

    @staticmethod
    def _documento(documento_id, expediente_id, tipo, ruta):
        return SimpleNamespace(
            id=documento_id,
            expediente_id=expediente_id,
            tipo=tipo,
            ruta=ruta,
        )

    @staticmethod
    def _datos(texto, orden_pago, cuit):
        return DatosOPExtraidos(
            texto_extraido=texto,
            paginas=1 if texto else 0,
            cuit=cuit if texto else None,
            fecha="11/08/2026" if texto else None,
            orden_pago=orden_pago if texto else None,
            liquidacion=None,
            proveedor="PROVEEDOR" if texto else None,
            fondo="Fondo Compensador" if texto else None,
            monto_total_facturas=12000.0 if texto else None,
            monto_neto_pagar=11000.0 if texto else None,
            importe_pago=None,
            importe_probable=None,
            importe_contexto=None,
            facturas=[],
            retenciones=[],
            advertencias=[],
        )

    @staticmethod
    def _expediente(configuracion_uc_id):
        return SimpleNamespace(
            creado=datetime(2026, 8, 11, 10),
            configuracion_uc_id=configuracion_uc_id,
        )

    @staticmethod
    def _resultado():
        rango = RangoProcedimientoUC(
            id_rango="rango-1",
            configuracion_uc_id="configuracion-1",
            limite_inferior=Decimal("0"),
            limite_superior=Decimal("1000000"),
            limite_inferior_inclusivo=True,
            limite_superior_inclusivo=True,
            procedimiento="PROCEDIMIENTO",
            articulo="ARTICULO",
            inciso="INCISO",
            referencia_normativa="REFERENCIA",
        )
        configuracion = ConfiguracionUC(
            id_configuracion="configuracion-1",
            fecha_inicio_vigencia=date(2026, 1, 1),
            fecha_fin_vigencia=None,
            valor_uc=Decimal("1000"),
            moneda="ARS",
            resolucion="RESOLUCION",
            organismo_emisor="ORGANISMO",
            estado="ACTIVA",
            rangos=(rango,),
        )
        return ResultadoDeterminacionProcedimiento(
            monto=Decimal("12000"),
            cantidad_uc=Decimal("12"),
            valor_uc=Decimal("1000"),
            configuracion=configuracion,
            rango=rango,
        )


if __name__ == "__main__":
    unittest.main()
