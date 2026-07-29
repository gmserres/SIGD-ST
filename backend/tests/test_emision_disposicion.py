import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
    MotivoNoHabilitacion,
)


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

    def test_emite_snapshots_fecha_y_fondo_de_decision(self):
        with patch(
            "app.services.emision_disposicion.STORAGE_DIR",
            Path("C:/app/storage"),
        ):
            self.docx.generar_docx.return_value = Path(
                "C:/app/storage/exports/EXP-1/disposicion.docx"
            )
            resultado = self.service.emitir("EXP-1")
        guardada = self.persistence.disposiciones[0]
        self.assertEqual(guardada.fecha_emision, self.fecha)
        self.assertEqual(guardada.fondo_interviniente, "CUFP")
        self.assertNotEqual(
            guardada.fondo_interviniente,
            self.analisis.analizar.return_value.fondo,
        )
        self.assertEqual(guardada.numero_op, "OP-1")
        self.assertEqual(guardada.numero_liquidacion, "LIQ-1")
        self.assertEqual(guardada.texto_emitido, "Texto final")
        self.assertEqual(
            guardada.ruta_docx,
            "exports/EXP-1/disposicion.docx",
        )
        self.assertEqual(
            resultado.estado,
            EstadoExpediente.DISPOSICION_EMITIDA,
        )

    def test_no_habilitado_impide_docx_y_persistencia(self):
        habilitacion = HabilitacionDisposicion(
            False,
            (
                MotivoNoHabilitacion(
                    "PENDIENTE_REVALIDACION",
                    "El Expediente requiere revalidación.",
                ),
            ),
        )
        self.evaluador.evaluar_para_emision.return_value = (
            habilitacion,
            ContextoEmisionDisposicion(
                expediente=self.expediente,
                decision=None,
                analisis_op=None,
            ),
        )
        with self.assertRaises(EmisionDisposicionError) as contexto:
            self.service.emitir("EXP-1")
        self.assertIs(contexto.exception.habilitacion, habilitacion)
        self.docx.generar_docx.assert_not_called()
        self.borradores.obtener.assert_not_called()
        self.assertEqual(self.persistence.disposiciones, [])
        self.evaluador.evaluar_para_emision.assert_called_once_with(
            "EXP-1"
        )

    def test_fallo_docx_no_llama_persistencia(self):
        self.docx.generar_docx.side_effect = RuntimeError("DOCX")
        with self.assertRaisesRegex(RuntimeError, "DOCX"):
            self.service.emitir("EXP-1")
        self.assertEqual(self.persistence.disposiciones, [])

    def test_docx_fuera_de_storage_se_elimina_y_no_persiste(self):
        with TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            storage = raiz / "storage"
            storage.mkdir()
            externo = raiz / "externo.docx"
            externo.write_bytes(b"DOCX")
            self.docx.generar_docx.return_value = externo
            with patch(
                "app.services.emision_disposicion.STORAGE_DIR",
                storage,
            ):
                with self.assertRaisesRegex(
                    EmisionDisposicionError,
                    "fuera del almacenamiento",
                ):
                    self.service.emitir("EXP-1")
            self.assertFalse(externo.exists())
            self.assertEqual(self.persistence.disposiciones, [])

    def test_fallo_persistencia_elimina_docx_generado(self):
        self.persistence.error = RuntimeError("SQL")
        with TemporaryDirectory() as temporal:
            storage = Path(temporal) / "storage"
            salida = (
                storage
                / "exports"
                / "EXP-1"
                / "disposicion.docx"
            )
            salida.parent.mkdir(parents=True)
            salida.write_bytes(b"DOCX")
            self.docx.generar_docx.return_value = salida
            with patch(
                "app.services.emision_disposicion.STORAGE_DIR",
                storage,
            ):
                with self.assertRaisesRegex(RuntimeError, "SQL"):
                    self.service.emitir("EXP-1")
            self.assertFalse(salida.exists())

    def test_normaliza_componentes_relativos_dentro_de_storage(self):
        with TemporaryDirectory() as temporal:
            storage = Path(temporal) / "storage"
            salida = (
                storage
                / "exports"
                / "temporal"
                / ".."
                / "EXP-1"
                / "disposicion.docx"
            )
            self.docx.generar_docx.return_value = salida
            with patch(
                "app.services.emision_disposicion.STORAGE_DIR",
                storage,
            ):
                self.service.emitir("EXP-1")
            self.assertEqual(
                self.persistence.disposiciones[0].ruta_docx,
                "exports/EXP-1/disposicion.docx",
            )

    def test_error_persistence_se_propaga(self):
        self.persistence.error = RuntimeError("SQL")
        with patch(
            "app.services.emision_disposicion.STORAGE_DIR",
            Path("C:/app/storage"),
        ):
            self.docx.generar_docx.return_value = Path(
                "C:/app/storage/exports/EXP-1/disposicion.docx"
            )
            with self.assertRaisesRegex(RuntimeError, "SQL"):
                self.service.emitir("EXP-1")


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
