import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.domain.habilitacion_proveedor_op import (
    EstadoHabilitacionProveedorOP,
)
from app.schemas.disposicion import DisposicionUpdate
from app.services.disposicion_docx import DisposicionDocxService
from app.services.disposiciones import (
    BorradorDisposicionNoHabilitadoError,
    BorradorDisposicionObsoletoError,
    DisposicionOPAmbiguaError,
    DisposicionOPNoEncontradaError,
    DisposicionService,
)


class BorradorDisposicionDireccionadoTest(unittest.TestCase):
    def setUp(self) -> None:
        objetivos = {
            "habilitar": (
                "app.services.disposiciones."
                "evaluar_habilitacion_proveedor_op_service.evaluar"
            ),
            "analizar": (
                "app.services.disposiciones."
                "analisis_op_service.reconstruir_documento"
            ),
            "expediente": (
                "app.services.disposiciones.expediente_service.obtener"
            ),
            "documento": (
                "app.services.disposiciones.documento_service.obtener_por_id"
            ),
            "listar_documentos": (
                "app.services.disposiciones."
                "documento_service.listar_por_expediente"
            ),
            "seleccion": (
                "app.services.disposiciones."
                "seleccion_proveedor_repository.obtener_por_id"
            ),
            "historial": (
                "app.services.disposiciones."
                "historial_service.listar_por_expediente"
            ),
            "registrar": (
                "app.services.disposiciones.historial_service.registrar"
            ),
            "parametros": (
                "app.services.disposiciones."
                "parametros_institucionales_service.obtener"
            ),
            "cargar": "app.services.disposiciones.template_engine.cargar",
            "renderizar": (
                "app.services.disposiciones.template_engine.renderizar"
            ),
            "dividir": "app.services.disposiciones.dividir_disposicion",
        }
        self.mocks = {}
        self.patchers = []
        for nombre, objetivo in objetivos.items():
            parche = patch(objetivo)
            self.patchers.append(parche)
            self.mocks[nombre] = parche.start()
        self.addCleanup(self._detener_patchers)

        self.mocks["expediente"].return_value = SimpleNamespace(
            id="EXP-1",
            numero_interno="EXP-1",
            numero_disposicion="1/2026",
            id_suna="1",
            objeto="Objeto",
            establecimiento="EP 1",
            configuracion_uc_id="UC-1",
        )
        self.mocks["historial"].return_value = []
        self.mocks["parametros"].return_value = SimpleNamespace(
            ejercicio=2026
        )
        self.mocks["cargar"].return_value = "plantilla"
        self.mocks["renderizar"].return_value = SimpleNamespace(
            contenido="contenido",
            variables_usadas={"A", "B"},
            variables_faltantes=set(),
        )
        self.mocks["dividir"].return_value = (
            "VISTO",
            "CONSIDERANDO",
            "DISPONE",
        )
        self.mocks["seleccion"].return_value = SimpleNamespace(
            id_seleccion="SEL-1",
            expediente_id="EXP-1",
            proveedor_razon_social="Razón selección histórica",
        )
        self.servicio = DisposicionService()
        self._configurar_documento("DOC-000001")

    def _detener_patchers(self) -> None:
        for parche in reversed(self.patchers):
            parche.stop()

    def test_op_a_genera_borrador_a(self) -> None:
        resultado = self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.assertEqual(resultado.documento_op_id, "DOC-000001")

    def test_op_b_genera_borrador_b(self) -> None:
        self._configurar_documento("DOC-000002", numero="OP-B")
        resultado = self.servicio.generar_borrador("EXP-1", "DOC-000002")
        self.assertEqual(resultado.documento_op_id, "DOC-000002")

    def test_borradores_a_y_b_coexisten(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self._configurar_documento("DOC-000002", numero="OP-B")
        self.servicio.generar_borrador("EXP-1", "DOC-000002")
        self.assertEqual(len(self.servicio._borradores), 2)

    def test_op_a_no_sobrescribe_b(self) -> None:
        self._configurar_documento("DOC-000002", numero="OP-B")
        borrador_b = self.servicio.generar_borrador("EXP-1", "DOC-000002")
        self._configurar_documento("DOC-000001", numero="OP-A")
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.assertIs(
            self.servicio._borradores[("EXP-1", "DOC-000002")],
            borrador_b,
        )

    def test_op_a_no_usa_datos_de_b(self) -> None:
        self._configurar_documento(
            "DOC-000001",
            numero="OP-A",
            importe=100,
            procedimiento="Procedimiento A",
            razon="Proveedor A",
        )
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        variables = self.mocks["renderizar"].call_args.args[1]
        self.assertEqual(variables["ORDEN_PAGO"], "OP-A")
        self.assertEqual(variables["PROVEEDOR"], "Proveedor A")
        self.assertIn("100", variables["IMPORTE"])
        self.assertEqual(variables["PROCEDIMIENTO"], "Procedimiento A")

    def test_habilitado_permite(self) -> None:
        self.assertFalse(
            self.servicio.generar_borrador(
                "EXP-1", "DOC-000001"
            ).obsoleto
        )

    def test_estados_no_habilitados_bloquean(self) -> None:
        estados = tuple(
            estado
            for estado in EstadoHabilitacionProveedorOP
            if estado != EstadoHabilitacionProveedorOP.HABILITADO
        )
        for estado in estados:
            with self.subTest(estado=estado):
                self.mocks["habilitar"].return_value = self._habilitacion(
                    "DOC-000001", estado=estado
                )
                with self.assertRaises(BorradorDisposicionNoHabilitadoError):
                    self.servicio.generar_borrador(
                        "EXP-1", "DOC-000001", regenerar=True
                    )

    def test_razon_op_presente_no_consulta_seleccion(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["seleccion"].assert_not_called()
        self.assertEqual(
            self.mocks["renderizar"].call_args.args[1]["PROVEEDOR"],
            "Proveedor A",
        )

    def test_razon_op_ausente_consulta_seleccion_habilitante(self) -> None:
        self.mocks["habilitar"].return_value = self._habilitacion(
            "DOC-000001", razon=None
        )
        resultado = self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["seleccion"].assert_called_once_with("SEL-1")
        self.assertEqual(
            self.mocks["renderizar"].call_args.args[1]["PROVEEDOR"],
            "Razón selección histórica",
        )
        self.assertIsNone(resultado.proveedor_definitivo_razon_social)

    def test_fallback_rechaza_otra_seleccion(self) -> None:
        self.mocks["habilitar"].return_value = self._habilitacion(
            "DOC-000001", razon=None
        )
        self.mocks["seleccion"].return_value = SimpleNamespace(
            id_seleccion="SEL-OTRA",
            proveedor_razon_social="Otra",
        )
        with self.assertRaises(RuntimeError):
            self.servicio.generar_borrador("EXP-1", "DOC-000001")

    def test_fallback_rechaza_seleccion_de_otro_expediente(self) -> None:
        self.mocks["habilitar"].return_value = self._habilitacion(
            "DOC-000001", razon=None
        )
        self.mocks["seleccion"].return_value = SimpleNamespace(
            id_seleccion="SEL-1",
            expediente_id="EXP-OTRO",
            proveedor_razon_social="Otra",
        )
        with self.assertRaisesRegex(RuntimeError, "no pertenece"):
            self.servicio.generar_borrador("EXP-1", "DOC-000001")

    def test_no_existe_dependencia_del_maestro(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.assertFalse(
            hasattr(self.servicio, "_proveedor_repository")
        )

    def test_borrador_conserva_trazabilidad_completa(self) -> None:
        resultado = self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.assertEqual(resultado.control_proveedor_op_id, "CTRL-1")
        self.assertEqual(resultado.seleccion_proveedor_id, "SEL-1")
        self.assertEqual(resultado.proveedor_definitivo_id, "PROV-1")
        self.assertEqual(resultado.proveedor_definitivo_cuit, "30718078063")

    def test_reconstruye_exclusivamente_documento_solicitado(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["analizar"].assert_called_once_with(
            "EXP-1", "DOC-000001"
        )

    def test_extraccion_secundaria_usa_documento_solicitado(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["documento"].assert_called_once_with("DOC-000001")
        self.mocks["listar_documentos"].assert_not_called()

    def test_conserva_configuracion_historica_del_expediente(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.assertEqual(
            self.mocks["expediente"].return_value.configuracion_uc_id,
            "UC-1",
        )

    def test_eventos_identifican_documento_op(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        detalles = [
            llamada.kwargs.get("detalle", "")
            for llamada in self.mocks["registrar"].call_args_list
        ]
        self.assertTrue(all("DOC-000001" in detalle for detalle in detalles))

    def test_get_marca_borrador_obsoleto(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["habilitar"].return_value = self._habilitacion(
            "DOC-000001",
            estado=EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL,
        )
        resultado = self.servicio.obtener_borrador("EXP-1", "DOC-000001")
        self.assertTrue(resultado.obsoleto)

    def test_put_bloquea_borrador_obsoleto(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["habilitar"].return_value = self._habilitacion(
            "DOC-000001", control="CTRL-2"
        )
        with self.assertRaises(BorradorDisposicionObsoletoError):
            self.servicio.actualizar_borrador(
                "EXP-1", "DOC-000001", DisposicionUpdate(visto="Otro")
            )

    def test_regenerar_reemplaza_contexto_obsoleto(self) -> None:
        self.servicio.generar_borrador("EXP-1", "DOC-000001")
        self.mocks["habilitar"].return_value = self._habilitacion(
            "DOC-000001", control="CTRL-2"
        )
        resultado = self.servicio.generar_borrador(
            "EXP-1", "DOC-000001", regenerar=True
        )
        self.assertEqual(resultado.control_proveedor_op_id, "CTRL-2")
        self.assertFalse(resultado.obsoleto)

    def test_legacy_una_op_delega(self) -> None:
        self.mocks["listar_documentos"].return_value = [
            SimpleNamespace(id="DOC-000001", tipo="OP")
        ]
        resultado = self.servicio.generar_borrador_legacy("EXP-1")
        self.assertEqual(resultado.documento_op_id, "DOC-000001")

    def test_legacy_cero_o_varias_op_rechaza(self) -> None:
        self.mocks["listar_documentos"].return_value = []
        with self.assertRaises(DisposicionOPNoEncontradaError):
            self.servicio.generar_borrador_legacy("EXP-1")
        self.mocks["listar_documentos"].return_value = [
            SimpleNamespace(id="DOC-1", tipo="OP"),
            SimpleNamespace(id="DOC-2", tipo="OP"),
        ]
        with self.assertRaises(DisposicionOPAmbiguaError):
            self.servicio.generar_borrador_legacy("EXP-1")

    def test_docx_a_y_b_quedan_separados_y_obsoleto_bloquea(self) -> None:
        with TemporaryDirectory() as temporal:
            docx = DisposicionDocxService(Path(temporal))
            borrador = SimpleNamespace(
                visto="VISTO", considerando="CONSIDERANDO", dispone="DISPONE"
            )
            with patch(
                "app.services.disposicion_docx.expediente_service.obtener",
                return_value=self.mocks["expediente"].return_value,
            ), patch(
                "app.services.disposicion_docx."
                "disposicion_service.obtener_exportable",
                return_value=borrador,
            ) as obtener, patch(
                "app.services.disposicion_docx.historial_service.registrar"
            ):
                salida_a = docx.generar_docx("EXP-1", "DOC-000001")
                salida_b = docx.generar_docx("EXP-1", "DOC-000002")
            self.assertNotEqual(salida_a.parent, salida_b.parent)
            self.assertEqual(salida_a.parent.name, "DOC-000001")
            self.assertEqual(salida_b.parent.name, "DOC-000002")
            self.assertEqual(obtener.call_count, 2)

    def _configurar_documento(
        self,
        documento_id: str,
        *,
        numero: str = "OP-A",
        importe: float = 100,
        procedimiento: str = "Procedimiento A",
        razon: str | None = "Proveedor A",
    ) -> None:
        self.mocks["habilitar"].return_value = self._habilitacion(
            documento_id, razon=razon
        )
        self.mocks["analizar"].return_value = SimpleNamespace(
            expediente_id="EXP-1",
            documento_op_id=documento_id,
            modo="PDF",
            op_detectada=True,
            proveedor=razon,
            cuit="30718078063",
            fondo="FONDO",
            orden_pago=numero,
            liquidacion="LIQ",
            fecha_op="01/08/2026",
            importe_bruto=importe,
            importe_neto=importe,
            valor_uc=100,
            norma_uc="Norma",
            cantidad_uc=1,
            procedimiento=procedimiento,
            articulo="18",
            inciso="C",
            documentos_comerciales=[],
            retenciones=[],
        )
        self.mocks["documento"].return_value = SimpleNamespace(
            id=documento_id,
            expediente_id="EXP-1",
            tipo="OP",
            ruta="ruta-inexistente.pdf",
        )

    @staticmethod
    def _habilitacion(
        documento_id: str,
        *,
        estado=EstadoHabilitacionProveedorOP.HABILITADO,
        razon="Proveedor A",
        control="CTRL-1",
    ):
        return SimpleNamespace(
            expediente_id="EXP-1",
            documento_op_id=documento_id,
            estado=estado,
            mensaje="Mensaje",
            proxima_accion="Acción",
            control_proveedor_op_id=control,
            seleccion_proveedor_id="SEL-1",
            proveedor_definitivo_id="PROV-1",
            proveedor_definitivo_cuit="30718078063",
            proveedor_definitivo_razon_social=razon,
        )
