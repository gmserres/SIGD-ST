import unittest
from datetime import datetime
from unittest.mock import MagicMock

from app.schemas.control_proveedor_op import (
    ControlProveedorOPRead,
    EstadoControlProveedorOPAdministrativo,
)
from app.services.registrar_control_proveedor_op_service import (
    RegistrarControlProveedorOPService,
)


CONTROL_ID = "00000000-0000-0000-0000-000000000501"
FECHA = datetime(2026, 8, 11, 15, 30)


class RegistrarControlProveedorOPServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.control_service = MagicMock()
        self.repository = MagicMock()
        self.service = RegistrarControlProveedorOPService(
            self.control_service,
            self.repository,
            ahora=lambda: FECHA,
            generar_id=lambda: CONTROL_ID,
        )
        self.control_service.ejecutar.return_value = self._resultado()
        self.repository.guardar.side_effect = lambda control: control

    def test_post_logico_persiste_resultado(self) -> None:
        resultado = self.service.ejecutar("EXP-1", "DOC-000001")

        self.repository.guardar.assert_called_once()
        self.assertEqual(resultado.id_control, CONTROL_ID)
        self.assertEqual(resultado.fecha_control, FECHA)

    def test_consulta_f3_no_persiste(self) -> None:
        self.control_service.consultar("EXP-1", "DOC-000001")

        self.repository.guardar.assert_not_called()

    def test_reejecucion_crea_dos_evidencias(self) -> None:
        ids = iter(
            (
                "00000000-0000-0000-0000-000000000501",
                "00000000-0000-0000-0000-000000000502",
            )
        )
        self.service._generar_id = lambda: next(ids)

        primero = self.service.ejecutar("EXP-1", "DOC-000001")
        segundo = self.service.ejecutar("EXP-1", "DOC-000001")

        self.assertEqual(self.repository.guardar.call_count, 2)
        self.assertNotEqual(primero.id_control, segundo.id_control)

    def test_sin_solicitud_no_persiste(self) -> None:
        self.control_service.ejecutar.return_value = self._resultado(
            estado=(
                EstadoControlProveedorOPAdministrativo
                .SIN_SOLICITUD_ASOCIADA
            ),
            solicitud_intervencion_id=None,
            seleccion_proveedor_id=None,
            cuit_seleccionado=None,
            razon_social_seleccionada=None,
            modo_analisis=None,
        )

        resultado = self.service.ejecutar("EXP-1", "DOC-000001")

        self.repository.guardar.assert_not_called()
        self.assertIsNone(resultado.id_control)
        self.assertIsNone(resultado.fecha_control)

    def test_sin_seleccion_no_persiste(self) -> None:
        self.control_service.ejecutar.return_value = self._resultado(
            estado=(
                EstadoControlProveedorOPAdministrativo
                .SIN_PROVEEDOR_SELECCIONADO
            ),
            seleccion_proveedor_id=None,
            cuit_seleccionado=None,
            razon_social_seleccionada=None,
            modo_analisis=None,
        )

        resultado = self.service.ejecutar("EXP-1", "DOC-000001")

        self.repository.guardar.assert_not_called()
        self.assertIsNone(resultado.id_control)

    def test_construye_evidencia_inmutable_con_snapshots(
        self,
    ) -> None:
        resultado = self.service.ejecutar("EXP-1", "DOC-000001")
        evidencia = self.repository.guardar.call_args.args[0]

        self.assertEqual(
            evidencia.proveedor_cuit_seleccionado, "30718078063"
        )
        self.assertEqual(
            evidencia.proveedor_razon_social_seleccionada,
            "Proveedor A",
        )
        self.assertEqual(evidencia.cuit_detectado, "30718078063")
        self.assertEqual(
            evidencia.razon_social_detectada, "Proveedor A"
        )
        self.assertEqual(evidencia.modo_analisis, "ALFA_PDF_TEXTO")
        self.assertEqual(resultado.modo_analisis, "ALFA_PDF_TEXTO")

    @staticmethod
    def _resultado(**cambios) -> ControlProveedorOPRead:
        valores = {
            "expediente_id": "EXP-1",
            "documento_op_id": "DOC-000001",
            "solicitud_intervencion_id": "SOL-1",
            "seleccion_proveedor_id": "SEL-1",
            "estado": EstadoControlProveedorOPAdministrativo.COINCIDE,
            "cuit_seleccionado": "30718078063",
            "cuit_detectado": "30718078063",
            "razon_social_seleccionada": "Proveedor A",
            "razon_social_detectada": "Proveedor A",
            "advertencias": [],
            "modo_analisis": "ALFA_PDF_TEXTO",
        }
        valores.update(cambios)
        return ControlProveedorOPRead(**valores)
