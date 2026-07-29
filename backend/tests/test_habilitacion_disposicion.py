import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from app.api.expedientes import generar_disposicion
from app.domain.estados import EstadoExpediente
from app.services.emision_disposicion import EmisionDisposicionError
from app.services.habilitacion_disposicion import (
    EvaluadorHabilitacionDisposicion,
    HabilitacionDisposicion,
    MotivoNoHabilitacion,
)


class EvaluadorHabilitacionDisposicionTest(unittest.TestCase):
    def setUp(self):
        self.expediente = SimpleNamespace(
            estado=EstadoExpediente.VALIDADO,
            numero_disposicion="1/2026",
            objeto="Compra",
            establecimiento="EP 1",
            decision_administrativa_id="DEC-1",
            configuracion_uc_id="CONFIG-1",
        )
        self.expedientes = MagicMock()
        self.expedientes.obtener.return_value = self.expediente
        self.decisiones = MagicMock()
        self.decisiones.obtener_por_id.return_value = SimpleNamespace(
            fondo_interviniente="FONDO_COMPENSADOR"
        )
        self.analisis = MagicMock()
        self.analisis.analizar.return_value = SimpleNamespace(
            orden_pago="OP-1",
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe_bruto=1000,
            valor_uc=1677,
            cantidad_uc=0.5963,
            procedimiento="Factura Conformada",
            norma_uc="Ley 13.981",
        )
        self.documentos = MagicMock()
        self.documentos.listar_por_expediente.return_value = [
            SimpleNamespace(tipo="OP")
        ]
        self.validaciones = MagicMock()
        self.validaciones.obtener_vigente.return_value = SimpleNamespace(
            id=1
        )
        self.evaluador = EvaluadorHabilitacionDisposicion(
            self.expedientes,
            self.decisiones,
            self.analisis,
            self.documentos,
            self.validaciones,
        )

    def codigos(self):
        return [
            motivo.codigo
            for motivo in self.evaluador.evaluar("EXP-1").motivos
        ]

    def test_expediente_habilitado(self):
        resultado = self.evaluador.evaluar("EXP-1")
        self.assertTrue(resultado.habilitada)
        self.assertEqual(resultado.motivos, ())

    def test_pendiente_revalidacion_siempre_bloquea(self):
        self.expediente.estado = EstadoExpediente.PENDIENTE_REVALIDACION
        self.validaciones.obtener_vigente.return_value = None
        self.assertEqual(
            self.codigos(),
            ["PENDIENTE_REVALIDACION"],
        )

    def test_validado_sin_acto_vigente(self):
        self.validaciones.obtener_vigente.return_value = None
        self.assertEqual(self.codigos(), ["SIN_VALIDACION_VIGENTE"])

    def test_acto_vigente_con_estado_incorrecto(self):
        self.expediente.estado = EstadoExpediente.PENDIENTE_VALIDACION
        self.assertEqual(self.codigos(), ["EXPEDIENTE_NO_VALIDADO"])

    def test_sin_op(self):
        self.documentos.listar_por_expediente.return_value = []
        self.assertEqual(self.codigos(), ["SIN_OP"])
        self.analisis.analizar.assert_not_called()

    def test_op_no_apta(self):
        self.analisis.analizar.return_value.proveedor = None
        self.assertEqual(self.codigos(), ["OP_NO_APTA"])

    def test_multiples_op_no_rompen_evaluacion(self):
        self.documentos.listar_por_expediente.return_value = [
            SimpleNamespace(tipo="OP"),
            SimpleNamespace(tipo="OP"),
        ]
        self.assertEqual(self.codigos(), [])
        self.analisis.analizar.assert_called_once_with("EXP-1")

    def test_datos_insuficientes(self):
        self.expediente.numero_disposicion = None
        self.assertEqual(self.codigos(), ["DATOS_INSUFICIENTES"])

    def test_motivos_multiples_tienen_orden_estable(self):
        self.expediente.estado = EstadoExpediente.BORRADOR
        self.expediente.numero_disposicion = None
        self.expediente.configuracion_uc_id = None
        self.validaciones.obtener_vigente.return_value = None
        self.documentos.listar_por_expediente.return_value = []
        self.assertEqual(
            self.codigos(),
            [
                "EXPEDIENTE_NO_VALIDADO",
                "SIN_VALIDACION_VIGENTE",
                "SIN_OP",
                "DATOS_INSUFICIENTES",
            ],
        )

    def test_evaluacion_no_modifica_datos(self):
        expediente_antes = deepcopy(self.expediente)
        self.evaluador.evaluar("EXP-1")
        self.assertEqual(self.expediente.__dict__, expediente_antes.__dict__)
        self.validaciones.invalidar_vigente.assert_not_called()

    def test_sin_configuracion_no_ejecuta_analisis_con_efecto_lateral(self):
        self.expediente.configuracion_uc_id = None
        self.assertEqual(self.codigos(), ["DATOS_INSUFICIENTES"])
        self.analisis.analizar.assert_not_called()

    def test_solo_considera_validacion_vigente(self):
        self.validaciones.obtener_vigente.return_value = None
        self.assertEqual(self.codigos(), ["SIN_VALIDACION_VIGENTE"])
        self.validaciones.obtener_vigente.assert_called_once_with("EXP-1")


class HabilitacionDisposicionApiTest(unittest.TestCase):
    def test_emision_no_habilitada_responde_conflicto_estructurado(self):
        habilitacion = HabilitacionDisposicion(
            False,
            (
                MotivoNoHabilitacion(
                    "SIN_VALIDACION_VIGENTE",
                    "El Expediente no posee validación vigente.",
                ),
            ),
        )
        service = MagicMock()
        service.emitir.side_effect = EmisionDisposicionError(habilitacion)
        with (
            patch(
                "app.api.expedientes.emision_disposicion_service",
                service,
            ),
            patch("app.api.expedientes.historial_service"),
            self.assertRaises(HTTPException) as contexto,
        ):
            generar_disposicion("EXP-1")
        self.assertEqual(contexto.exception.status_code, 409)
        self.assertEqual(
            contexto.exception.detail,
            {
                "habilitada": False,
                "motivos": [
                    {
                        "codigo": "SIN_VALIDACION_VIGENTE",
                        "descripcion": (
                            "El Expediente no posee validación vigente."
                        ),
                    }
                ],
            },
        )
