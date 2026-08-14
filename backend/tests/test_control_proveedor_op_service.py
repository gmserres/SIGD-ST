import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from app.domain.control_proveedor_op import (
    ADVERTENCIA_RAZON_SOCIAL_DIFERENTE,
)
from app.schemas.control_proveedor_op import (
    EstadoControlProveedorOPAdministrativo,
)
from app.services.analisis_op import (
    ArchivoOPNoAnalizableError,
    ArchivoOPNoDisponibleError,
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)
from app.services.control_proveedor_op_service import (
    ControlProveedorOPService,
)


class ControlProveedorOPServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.expedientes = MagicMock()
        self.documentos = MagicMock()
        self.selecciones = MagicMock()
        self.analisis = MagicMock()
        self.expedientes.obtener.return_value = SimpleNamespace(
            solicitud_intervencion_id="SOL-1"
        )
        self.documentos.obtener_por_id.return_value = (
            SimpleNamespace(
                id="DOC-1",
                expediente_id="EXP-1",
                tipo="OP",
            )
        )
        self.seleccion = SimpleNamespace(
            id_seleccion="SEL-B",
            expediente_id="EXP-1",
            solicitud_intervencion_id="SOL-1",
            proveedor_cuit="30718078063",
            proveedor_razon_social="Proveedor B S.R.L.",
            vigente=True,
        )
        self.selecciones.obtener_vigente_por_expediente.return_value = (
            self.seleccion
        )
        self.analisis.analizar_documento.return_value = (
            self._analisis()
        )
        self.analisis.reconstruir_documento.return_value = (
            self._analisis()
        )
        self.servicio = ControlProveedorOPService(
            expediente_service=self.expedientes,
            documento_service=self.documentos,
            seleccion_proveedor_repository=self.selecciones,
            analisis_op_service=self.analisis,
        )

    def test_cuit_coincidente(self) -> None:
        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOPAdministrativo.COINCIDE,
        )

    def test_cuit_diferente(self) -> None:
        self.analisis.analizar_documento.return_value = (
            self._analisis(cuit="30699999991")
        )

        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOPAdministrativo.CUIT_DIFERENTE,
        )

    def test_op_sin_cuit(self) -> None:
        self.analisis.analizar_documento.return_value = (
            self._analisis(cuit=None)
        )

        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOPAdministrativo.NO_VERIFICABLE,
        )

    def test_expediente_sin_solicitud_no_lee_op(self) -> None:
        self.expedientes.obtener.return_value = SimpleNamespace(
            solicitud_intervencion_id=None
        )

        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            (
                EstadoControlProveedorOPAdministrativo
                .SIN_SOLICITUD_ASOCIADA
            ),
        )
        self.selecciones.obtener_vigente_por_expediente.assert_not_called()
        self.analisis.analizar_documento.assert_not_called()

    def test_solicitud_sin_seleccion_no_lee_op(self) -> None:
        self.selecciones.obtener_vigente_por_expediente.return_value = (
            None
        )

        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            (
                EstadoControlProveedorOPAdministrativo
                .SIN_PROVEEDOR_SELECCIONADO
            ),
        )
        self.analisis.analizar_documento.assert_not_called()

    def test_consulta_exclusivamente_seleccion_vigente(
        self,
    ) -> None:
        self.servicio.ejecutar("EXP-1", "DOC-1")

        (
            self.selecciones.obtener_vigente_por_expediente
            .assert_called_once_with("EXP-1")
        )
        self.assertFalse(
            self.selecciones.listar_por_expediente.called
        )

    def test_reemplazo_previo_usa_nueva_seleccion(self) -> None:
        self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            self.analisis.analizar_documento.call_count,
            1,
        )
        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.seleccion_proveedor_id,
            "SEL-B",
        )
        self.assertEqual(
            resultado.cuit_seleccionado,
            self.seleccion.proveedor_cuit,
        )

    def test_inactivacion_posterior_del_maestro_es_irrelevante(
        self,
    ) -> None:
        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOPAdministrativo.COINCIDE,
        )
        self.assertEqual(resultado.seleccion_proveedor_id, "SEL-B")

    def test_cuit_detectado_con_guiones(self) -> None:
        self.analisis.analizar_documento.return_value = (
            self._analisis(cuit="30-71807806-3")
        )

        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOPAdministrativo.COINCIDE,
        )
        self.assertEqual(resultado.cuit_detectado, "30718078063")

    def test_razon_social_diferente_advierte(self) -> None:
        self.analisis.analizar_documento.return_value = (
            self._analisis(proveedor="Otra Empresa S.A.")
        )

        resultado = self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOPAdministrativo.COINCIDE,
        )
        self.assertEqual(
            resultado.advertencias,
            [ADVERTENCIA_RAZON_SOCIAL_DIFERENTE],
        )

    def test_ejecutar_usa_analizar_documento(self) -> None:
        self.servicio.ejecutar("EXP-1", "DOC-1")

        self.analisis.analizar_documento.assert_called_once_with(
            "EXP-1",
            "DOC-1",
        )
        self.analisis.reconstruir_documento.assert_not_called()

    def test_consultar_usa_reconstruir_documento(self) -> None:
        self.servicio.consultar("EXP-1", "DOC-1")

        self.analisis.reconstruir_documento.assert_called_once_with(
            "EXP-1",
            "DOC-1",
        )
        self.analisis.analizar_documento.assert_not_called()

    def test_siempre_respeta_documento_op_id(self) -> None:
        self.servicio.ejecutar("EXP-1", "DOC-1")
        self.servicio.consultar("EXP-1", "DOC-1")

        self.analisis.analizar_documento.assert_called_once_with(
            "EXP-1",
            "DOC-1",
        )
        self.analisis.reconstruir_documento.assert_called_once_with(
            "EXP-1",
            "DOC-1",
        )

    def test_propaga_errores_f1(self) -> None:
        errores = (
            DocumentoOPNoEncontradoError("DOC-1"),
            DocumentoOPExpedienteInconsistenteError(
                "DOC-1",
                "EXP-1",
            ),
            DocumentoNoEsOPError("DOC-1"),
            ArchivoOPNoDisponibleError("DOC-1"),
            ArchivoOPNoAnalizableError("DOC-1"),
        )

        for error in errores:
            with self.subTest(error=type(error).__name__):
                self.analisis.analizar_documento.side_effect = (
                    error
                )
                with self.assertRaises(type(error)):
                    self.servicio.ejecutar("EXP-1", "DOC-1")
                self.analisis.analizar_documento.reset_mock(
                    side_effect=True
                )

    def test_no_persiste_resultado(self) -> None:
        self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            self.selecciones.method_calls,
            [call.obtener_vigente_por_expediente("EXP-1")],
        )

    def test_no_modifica_seleccion(self) -> None:
        antes = deepcopy(self.seleccion)

        self.servicio.ejecutar("EXP-1", "DOC-1")

        self.assertEqual(
            self.seleccion.__dict__,
            antes.__dict__,
        )

    @staticmethod
    def _analisis(
        *,
        cuit: str | None = "30718078063",
        proveedor: str | None = "Proveedor B S.R.L.",
    ):
        return SimpleNamespace(
            documento_op_id="DOC-1",
            cuit=cuit,
            proveedor=proveedor,
        )
