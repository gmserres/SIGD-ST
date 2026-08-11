import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from app.domain.control_proveedor_op import EstadoControlProveedorOP
from app.domain.habilitacion_proveedor_op import EstadoHabilitacionProveedorOP
from app.services.evaluar_habilitacion_proveedor_op_service import (
    EvaluarHabilitacionProveedorOPService,
)


class HabilitacionProveedorOPServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.expedientes = MagicMock()
        self.documentos = MagicMock()
        self.selecciones = MagicMock()
        self.controles = MagicMock()
        self.proveedores = MagicMock()
        self.expedientes.obtener.return_value = SimpleNamespace(
            solicitud_intervencion_id="SOL-1"
        )
        self.documentos.obtener_por_id.return_value = SimpleNamespace(
            id="DOC-1", expediente_id="EXP-1", tipo="OP"
        )
        self.seleccion = self._seleccion()
        self.selecciones.obtener_vigente_por_solicitud.return_value = self.seleccion
        self.controles.obtener_ultimo_por_documento.return_value = self._control()
        self.proveedores.obtener_por_cuit.return_value = None
        self.servicio = EvaluarHabilitacionProveedorOPService(
            self.expedientes,
            self.documentos,
            self.selecciones,
            self.controles,
            self.proveedores,
        )

    def test_coincide_habilita_con_identidad_y_snapshots_op(self) -> None:
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(resultado.estado, EstadoHabilitacionProveedorOP.HABILITADO)
        self.assertEqual(resultado.proveedor_definitivo_id, "PROV-A")
        self.assertEqual(resultado.proveedor_definitivo_cuit, "30718078063")
        self.assertEqual(
            resultado.proveedor_definitivo_razon_social,
            "Proveedor documental A S.A.",
        )
        self.proveedores.obtener_por_cuit.assert_not_called()

    def test_cuit_diferente_requiere_reasignacion_sin_reasignar(self) -> None:
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            estado=EstadoControlProveedorOP.CUIT_DIFERENTE,
            cuit_detectado="30699999991",
            razon_social_detectada="Proveedor B S.R.L.",
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.REQUIERE_REASIGNACION_PROVEEDOR,
        )
        self.assertFalse(resultado.proveedor_op_en_maestro)
        self.assertEqual(
            self.selecciones.method_calls,
            [call.obtener_vigente_por_solicitud("SOL-1")],
        )

    def test_reasignacion_sin_nuevo_control_requiere_control(self) -> None:
        self.selecciones.obtener_vigente_por_solicitud.return_value = self._seleccion(
            id_seleccion="SEL-B", proveedor_id="PROV-B"
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL,
        )
        self.assertEqual(resultado.seleccion_proveedor_id, "SEL-B")

    def test_reasignacion_y_nuevo_coincide_habilita(self) -> None:
        self.selecciones.obtener_vigente_por_solicitud.return_value = self._seleccion(
            id_seleccion="SEL-B", proveedor_id="PROV-B"
        )
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            seleccion_proveedor_id="SEL-B",
            cuit_detectado="30699999991",
            razon_social_detectada="Proveedor B S.R.L.",
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(resultado.estado, EstadoHabilitacionProveedorOP.HABILITADO)
        self.assertEqual(resultado.proveedor_definitivo_id, "PROV-B")

    def test_coincide_historico_con_seleccion_reemplazada_no_habilita(self) -> None:
        self.selecciones.obtener_vigente_por_solicitud.return_value = self._seleccion(
            id_seleccion="SEL-B", proveedor_id="PROV-B"
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL,
        )

    def test_no_verificable_bloquea(self) -> None:
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            estado=EstadoControlProveedorOP.NO_VERIFICABLE,
            cuit_detectado=None,
            razon_social_detectada=None,
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.PROVEEDOR_NO_VERIFICABLE,
        )

    def test_sin_seleccion_requiere_seleccion(self) -> None:
        self.selecciones.obtener_vigente_por_solicitud.return_value = None
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.REQUIERE_SELECCION_PROVEEDOR,
        )
        self.controles.obtener_ultimo_por_documento.assert_not_called()

    def test_sin_solicitud_bloquea(self) -> None:
        self.expedientes.obtener.return_value = SimpleNamespace(
            solicitud_intervencion_id=None
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.SIN_SOLICITUD_ASOCIADA,
        )
        self.selecciones.obtener_vigente_por_solicitud.assert_not_called()

    def test_solo_importa_ultimo_control_autoritativo(self) -> None:
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            id_control="CTRL-3"
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(resultado.control_proveedor_op_id, "CTRL-3")
        self.assertFalse(self.controles.listar_por_documento.called)

    def test_discrepancia_historica_y_coincide_actual_habilita(self) -> None:
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            id_control="CTRL-COINCIDE"
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(resultado.estado, EstadoHabilitacionProveedorOP.HABILITADO)
        self.assertEqual(resultado.control_proveedor_op_id, "CTRL-COINCIDE")

    def test_op_a_habilitada_no_habilita_op_b(self) -> None:
        self.documentos.obtener_por_id.return_value = SimpleNamespace(
            id="DOC-B", expediente_id="EXP-1", tipo="OP"
        )
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            documento_op_id="DOC-A"
        )
        resultado = self.servicio.evaluar("EXP-1", "DOC-B")
        self.assertEqual(
            resultado.estado,
            EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL,
        )
        self.controles.obtener_ultimo_por_documento.assert_called_once_with("DOC-B")

    def test_proveedor_op_ausente_o_inactivo_en_maestro(self) -> None:
        self.controles.obtener_ultimo_por_documento.return_value = self._control(
            estado=EstadoControlProveedorOP.CUIT_DIFERENTE,
            cuit_detectado="30699999991",
        )
        casos = (
            (None, False, None),
            (SimpleNamespace(id_proveedor="PROV-B", activo=False), True, False),
        )
        for proveedor, existe, activo in casos:
            with self.subTest(existe=existe):
                self.proveedores.obtener_por_cuit.return_value = proveedor
                resultado = self.servicio.evaluar("EXP-1", "DOC-1")
                self.assertEqual(resultado.proveedor_op_en_maestro, existe)
                self.assertEqual(resultado.proveedor_op_activo, activo)

    def test_maestro_modificado_no_altera_snapshots_y_razon_op_puede_faltar(self) -> None:
        for razon_op in ("Razón histórica de la OP", None):
            with self.subTest(razon_op=razon_op):
                self.controles.obtener_ultimo_por_documento.return_value = self._control(
                    razon_social_detectada=razon_op
                )
                resultado = self.servicio.evaluar("EXP-1", "DOC-1")
                self.assertEqual(
                    resultado.estado, EstadoHabilitacionProveedorOP.HABILITADO
                )
                self.assertEqual(resultado.proveedor_definitivo_id, "PROV-A")
                self.assertEqual(resultado.proveedor_definitivo_cuit, "30718078063")
                self.assertEqual(
                    resultado.proveedor_definitivo_razon_social, razon_op
                )
        self.proveedores.obtener_por_cuit.assert_not_called()

    def test_evaluacion_es_determinista_y_no_modifica_fuentes(self) -> None:
        seleccion_antes = deepcopy(self.seleccion)
        control = self.controles.obtener_ultimo_por_documento.return_value
        control_antes = deepcopy(control)
        primero = self.servicio.evaluar("EXP-1", "DOC-1")
        segundo = self.servicio.evaluar("EXP-1", "DOC-1")
        self.assertEqual(primero, segundo)
        self.assertEqual(self.seleccion.__dict__, seleccion_antes.__dict__)
        self.assertEqual(control.__dict__, control_antes.__dict__)

    @staticmethod
    def _seleccion(**cambios):
        valores = {
            "id_seleccion": "SEL-A",
            "solicitud_intervencion_id": "SOL-1",
            "proveedor_id": "PROV-A",
            "proveedor_cuit": "30718078063",
            "proveedor_razon_social": "Proveedor actual del Maestro",
            "vigente": True,
        }
        valores.update(cambios)
        return SimpleNamespace(**valores)

    @staticmethod
    def _control(**cambios):
        valores = {
            "id_control": "CTRL-1",
            "expediente_id": "EXP-1",
            "documento_op_id": "DOC-1",
            "solicitud_intervencion_id": "SOL-1",
            "seleccion_proveedor_id": "SEL-A",
            "estado": EstadoControlProveedorOP.COINCIDE,
            "cuit_detectado": "30718078063",
            "razon_social_detectada": "Proveedor documental A S.A.",
        }
        valores.update(cambios)
        return SimpleNamespace(**valores)
