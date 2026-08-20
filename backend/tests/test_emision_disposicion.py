import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.repositories.disposicion_in_memory_repository import (
    InMemoryDisposicionRepository,
)
from app.services.consulta_disposicion import (
    ConsultaDisposicionService,
    DisposicionEmitidaNoEncontradaError,
)
from app.services.emision_disposicion import (
    EmisionDisposicionError,
    EmisionDisposicionService,
)
from app.services.habilitacion_disposicion import (
    ContextoEmisionDisposicion,
    HabilitacionDisposicion,
)
from app.api.expedientes import generar_disposicion


class FakeEmitirDisposicionPersistence:
    def __init__(self, expediente):
        self.expediente = expediente
        self.disposiciones = []
        self.error = None

    def emitir(self, disposicion, expediente_id):
        if self.error is not None:
            raise self.error
        self.disposiciones.append(disposicion)
        return replace(
            self.expediente,
            estado=EstadoExpediente.DISPOSICION_EMITIDA,
        )


class EmisionDisposicionServiceTest(unittest.TestCase):
    def setUp(self):
        self.fecha = datetime(2026, 7, 28, 12, 30)
        self.expediente = Expediente(
            id="EXP-1",
            numero_interno="033-1/2026",
            numero_gdeba=None,
            solicitud_intervencion_id="SOL-1",
            decision_administrativa_id="DEC-1",
            configuracion_uc_id="configuracion-1",
            id_suna="1",
            tipo_tramite="FONDO_COMPENSADOR",
            estado=EstadoExpediente.VALIDADO,
            establecimiento="EP 1",
            objeto="Objeto",
            numero_disposicion="1/2026",
            creado=datetime(2026, 7, 28, 9),
        )
        self.expedientes = MagicMock()
        self.expedientes.obtener.return_value = SimpleNamespace(
            **self.expediente.__dict__
        )
        self.decisiones = MagicMock()
        self.decisiones.obtener_por_id.return_value = SimpleNamespace(
            fondo_interviniente="CUFP"
        )
        self.analisis = MagicMock()
        self.analisis.analizar.return_value = SimpleNamespace(
            orden_pago="OP-1",
            liquidacion="LIQ-1",
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe_bruto=1000.50,
            valor_uc=Decimal("1677"),
            cantidad_uc=Decimal("0.59660"),
            procedimiento="Factura Conformada",
            norma_uc="Ley 13.981",
            fondo="Fondo Compensador",
        )
        self.borradores = MagicMock()
        self.borradores.obtener.return_value = SimpleNamespace()
        self.docx = MagicMock()
        self.docx.construir_texto_emitido.return_value = "Texto final"
        self.evaluador = MagicMock()
        self.evaluador.evaluar_para_emision.return_value = (
            HabilitacionDisposicion(True, ()),
            ContextoEmisionDisposicion(
                expediente=SimpleNamespace(**self.expediente.__dict__),
                decision=self.decisiones.obtener_por_id.return_value,
                analisis_op=self.analisis.analizar.return_value,
            ),
        )
        self.persistence = FakeEmitirDisposicionPersistence(
            self.expediente
        )
        self.service = EmisionDisposicionService(
            self.evaluador,
            self.borradores,
            self.docx,
            self.persistence,
            now=lambda: self.fecha,
        )

    def _rechazar_legacy(self):
        with self.assertRaisesRegex(
            EmisionDisposicionError,
            "Utilice una OP concreta",
        ):
            self.service.emitir("EXP-1")

    def test_emision_global_legacy_esta_deshabilitada(self):
        self._rechazar_legacy()

    def test_emision_global_no_evalua_habilitacion(self):
        self._rechazar_legacy()
        self.evaluador.evaluar_para_emision.assert_not_called()

    def test_emision_global_no_obtiene_borrador(self):
        self._rechazar_legacy()
        self.borradores.obtener.assert_not_called()

    def test_emision_global_no_construye_texto(self):
        self._rechazar_legacy()
        self.docx.construir_texto_emitido.assert_not_called()

    def test_emision_global_no_genera_docx(self):
        self._rechazar_legacy()
        self.docx.generar_docx.assert_not_called()

    def test_emision_global_no_persiste_disposicion(self):
        self._rechazar_legacy()
        self.assertEqual(self.persistence.disposiciones, [])

    def test_metodo_legacy_directo_tambien_esta_deshabilitado(self):
        with self.assertRaisesRegex(
            EmisionDisposicionError,
            "Utilice una OP concreta",
        ):
            self.service.emitir_legacy("EXP-1")


class ConsultaDisposicionServiceTest(unittest.TestCase):
    def test_recupera_snapshot_sin_dependencias_de_generacion(self):
        repository = InMemoryDisposicionRepository()
        disposicion = self._crear_disposicion()
        repository.guardar(disposicion)
        consulta = ConsultaDisposicionService(repository)
        recuperada = consulta.obtener_por_expediente("EXP-1")
        self.assertEqual(recuperada.texto_emitido, "Texto final")
        self.assertFalse(hasattr(consulta, "_borradores"))
        self.assertFalse(hasattr(consulta, "_analisis_op"))
        self.assertFalse(hasattr(consulta, "_docx"))

    def test_error_si_no_existe_aunque_haya_borrador_en_memoria(self):
        consulta = ConsultaDisposicionService(
            InMemoryDisposicionRepository()
        )
        with self.assertRaises(DisposicionEmitidaNoEncontradaError):
            consulta.obtener_por_expediente("EXP-1")

    @staticmethod
    def _crear_disposicion() -> Disposicion:
        return Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000001",
            expediente_id="EXP-1",
            configuracion_uc_id="configuracion-1",
            numero_disposicion="1/2026",
            fecha_emision=datetime(2026, 7, 28, 12, 30),
            fondo_interviniente="CUFP",
            numero_op="OP-1",
            numero_liquidacion=None,
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe=Decimal("1000"),
            objeto="Objeto",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.59660"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="Texto final",
            ruta_docx="exports/EXP-1/disposicion.docx",
        )


class EmisionDisposicionLegacyApiTest(unittest.TestCase):
    def test_endpoint_legacy_responde_conflicto(self):
        with patch(
            "app.api.expedientes.emision_disposicion_service.emitir",
            side_effect=EmisionDisposicionError(
                "La emisión global está deshabilitada."
            ),
        ):
            with self.assertRaises(HTTPException) as contexto:
                generar_disposicion("EXP-1")

        self.assertEqual(contexto.exception.status_code, 409)
