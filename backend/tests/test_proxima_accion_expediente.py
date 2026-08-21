import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import Mock

from app.domain.estados import EstadoExpediente
from app.domain.habilitacion_proveedor_op import EstadoHabilitacionProveedorOP
from app.schemas.expediente import ExpedienteRead
from app.schemas.proxima_accion_expediente import CodigoProximaAccionExpediente as Codigo
from app.services.proxima_accion_expediente import ProximaAccionExpedienteService


class ProximaAccionExpedienteTest(unittest.TestCase):
    def setUp(self):
        self.expedientes = Mock()
        self.documentos = Mock()
        self.validaciones = Mock()
        self.habilitaciones = Mock()
        self.disposiciones = Mock()
        self.service = ProximaAccionExpedienteService(
            self.expedientes,
            self.documentos,
            self.validaciones,
            self.habilitaciones,
            self.disposiciones,
        )
        self.documentos.listar_por_expediente.return_value = []
        self.validaciones.obtener_vigente.return_value = object()
        self.disposiciones.listar_por_expediente.return_value = []

    @staticmethod
    def expediente(estado=EstadoExpediente.VALIDADO, expediente_id="EXP-A", **cambios):
        datos = dict(
            id=expediente_id,
            numero_interno=f"{expediente_id}/2026",
            numero_gdeba="EX-2026",
            solicitud_intervencion_id="SOL-1",
            decision_administrativa_id="DEC-1",
            configuracion_uc_id=None,
            id_suna=None,
            tipo_tramite="FONDO_COMPENSADOR",
            estado=estado,
            establecimiento="EP 1",
            objeto="Objeto",
            numero_disposicion=None,
            creado=datetime(2026, 8, 1),
        )
        datos.update(cambios)
        return ExpedienteRead(**datos)

    @staticmethod
    def op(documento_id="DOC-1"):
        return SimpleNamespace(id=documento_id, tipo="OP")

    @staticmethod
    def habilitacion(estado):
        return SimpleNamespace(estado=estado)

    @staticmethod
    def disposicion(documento_id="DOC-1", formalizada=False):
        return SimpleNamespace(
            documento_op_id=documento_id,
            fecha_formalizacion=date(2026, 8, 20) if formalizada else None,
        )

    def derivar(self, expediente=None):
        expediente = expediente or self.expediente()
        self.expedientes.obtener.return_value = expediente
        return self.service.obtener(expediente.id)

    def configurar_op(self, estado, documento_id="DOC-1", disposicion=None):
        self.documentos.listar_por_expediente.return_value = [self.op(documento_id)]
        self.habilitaciones.evaluar.return_value = self.habilitacion(estado)
        self.disposiciones.listar_por_expediente.return_value = (
            [disposicion] if disposicion else []
        )

    def test_pendiente_revalidacion_prevalece(self):
        resultado = self.derivar(self.expediente(EstadoExpediente.PENDIENTE_REVALIDACION))
        self.assertEqual(resultado.codigo, Codigo.REVALIDAR_EXPEDIENTE)
        self.documentos.listar_por_expediente.assert_not_called()

    def test_op_sin_control_requiere_controlar(self):
        self.configurar_op(EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL)
        self.assertEqual(self.derivar().codigo, Codigo.CONTROLAR_PROVEEDOR)

    def test_cuit_diferente_requiere_regularizar(self):
        self.configurar_op(EstadoHabilitacionProveedorOP.REQUIERE_REASIGNACION_PROVEEDOR)
        self.assertEqual(self.derivar().codigo, Codigo.REGULARIZAR_PROVEEDOR)

    def test_no_verificable_requiere_revisar_documentacion(self):
        self.configurar_op(EstadoHabilitacionProveedorOP.PROVEEDOR_NO_VERIFICABLE)
        self.assertEqual(self.derivar().codigo, Codigo.REVISAR_DOCUMENTACION_OP)

    def test_f5_habilitado_sin_disposicion_requiere_prepararla(self):
        self.configurar_op(EstadoHabilitacionProveedorOP.HABILITADO)
        self.assertEqual(self.derivar().codigo, Codigo.PREPARAR_DISPOSICION)

    def test_disposicion_emitida_requiere_formalizacion(self):
        self.configurar_op(
            EstadoHabilitacionProveedorOP.HABILITADO,
            disposicion=self.disposicion(),
        )
        self.assertEqual(self.derivar().codigo, Codigo.REGISTRAR_FORMALIZACION)

    def test_todas_formalizadas_habilitan_cierre(self):
        self.configurar_op(
            EstadoHabilitacionProveedorOP.HABILITADO,
            disposicion=self.disposicion(formalizada=True),
        )
        self.assertEqual(self.derivar().codigo, Codigo.CERRAR_EXPEDIENTE)

    def test_cerrado_requiere_archivo(self):
        self.assertEqual(self.derivar(self.expediente(EstadoExpediente.CERRADO)).codigo, Codigo.ARCHIVAR_EXPEDIENTE)

    def test_desistido_requiere_archivo(self):
        self.assertEqual(self.derivar(self.expediente(EstadoExpediente.DESISTIDO)).codigo, Codigo.ARCHIVAR_EXPEDIENTE)

    def test_archivado_nuevo_es_consulta_historica(self):
        expediente = self.expediente(EstadoExpediente.ARCHIVADO, fecha_cierre=date(2026, 8, 20))
        self.assertEqual(self.derivar(expediente).codigo, Codigo.CONSULTAR_HISTORIAL)

    def test_disposicion_emitida_legacy_requiere_firma(self):
        resultado = self.derivar(self.expediente(EstadoExpediente.DISPOSICION_EMITIDA))
        self.assertEqual(resultado.codigo, Codigo.REGISTRAR_FIRMA_LEGACY)
        self.assertTrue(resultado.circuito_legacy)

    def test_firmado_legacy_requiere_archivo(self):
        resultado = self.derivar(self.expediente(EstadoExpediente.FIRMADO))
        self.assertEqual(resultado.codigo, Codigo.ARCHIVAR_EXPEDIENTE)
        self.assertTrue(resultado.circuito_legacy)

    def test_archivado_legacy_es_consulta_historica(self):
        resultado = self.derivar(self.expediente(EstadoExpediente.ARCHIVADO))
        self.assertEqual(resultado.codigo, Codigo.CONSULTAR_HISTORIAL)
        self.assertTrue(resultado.circuito_legacy)

    def test_varias_op_priorizan_discrepancia_sin_depender_del_orden(self):
        self.documentos.listar_por_expediente.return_value = [self.op("DOC-B"), self.op("DOC-A")]
        estados = {
            "DOC-A": EstadoHabilitacionProveedorOP.HABILITADO,
            "DOC-B": EstadoHabilitacionProveedorOP.REQUIERE_REASIGNACION_PROVEEDOR,
        }
        self.habilitaciones.evaluar.side_effect = lambda _exp, doc: self.habilitacion(estados[doc])
        self.disposiciones.listar_por_expediente.return_value = [self.disposicion("DOC-A")]
        resultado = self.derivar()
        self.assertEqual(resultado.codigo, Codigo.REGULARIZAR_PROVEEDOR)
        self.assertEqual(resultado.documento_op_id, "DOC-B")

    def test_empate_entre_op_se_resuelve_por_identidad_documental(self):
        self.documentos.listar_por_expediente.return_value = [self.op("DOC-B"), self.op("DOC-A")]
        self.habilitaciones.evaluar.return_value = self.habilitacion(EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL)
        resultado = self.derivar()
        self.assertEqual(resultado.documento_op_id, "DOC-A")

    def test_solicitud_uno_a_n_permanece_aislada_por_expediente(self):
        expediente_a = self.expediente(expediente_id="EXP-A")
        expediente_b = self.expediente(expediente_id="EXP-B")
        self.expedientes.listar.return_value = [expediente_a, expediente_b]
        self.documentos.listar_por_expediente.side_effect = lambda exp: [self.op(f"DOC-{exp[-1]}")]
        self.habilitaciones.evaluar.side_effect = lambda exp, _doc: self.habilitacion(
            EstadoHabilitacionProveedorOP.REQUIERE_REASIGNACION_PROVEEDOR
            if exp == "EXP-A" else EstadoHabilitacionProveedorOP.HABILITADO
        )
        resultados = {resultado.expediente_id: resultado for resultado in self.service.listar()}
        self.assertEqual(resultados["EXP-A"].codigo, Codigo.REGULARIZAR_PROVEEDOR)
        self.assertEqual(resultados["EXP-B"].codigo, Codigo.PREPARAR_DISPOSICION)

    def test_no_depende_de_historial_service(self):
        dependencias = vars(self.service)
        self.assertFalse(any("historial" in nombre.lower() for nombre in dependencias))


if __name__ == "__main__":
    unittest.main()
