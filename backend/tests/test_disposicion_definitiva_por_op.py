import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.expedientes import (
    emitir_disposicion_documento,
    obtener_disposicion_emitida_documento,
)
from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.domain.habilitacion_proveedor_op import EstadoHabilitacionProveedorOP
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.control_proveedor_op_model import ControlProveedorOPModel
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.seleccion_proveedor_model import SeleccionProveedorModel
from app.infrastructure.database.persistence.emitir_disposicion_postgres import PostgresEmitirDisposicionPersistence
from app.repositories.emitir_disposicion_persistence import ContextoEmisionObsoletoError
from app.schemas.disposicion import (
    DisposicionEmitirCreate,
    DisposicionRead,
)
from app.services.consulta_disposicion import (
    ConsultaDisposicionService,
    DisposicionEmitidaNoEncontradaError,
)
from app.services.disposiciones import BorradorDisposicionObsoletoError
from app.services.emision_disposicion import (
    EmisionDisposicionError,
    EmisionDisposicionService,
    EmisionProveedorOPNoHabilitadoError,
)
from app.services.habilitacion_disposicion import (
    ContextoEmisionDisposicion,
    HabilitacionDisposicion,
)


class FakePersistence:
    def __init__(self) -> None:
        self.guardadas: list[Disposicion] = []
        self.error: Exception | None = None

    def emitir(self, disposicion, expediente_id):
        if self.error is not None:
            raise self.error
        self.guardadas.append(disposicion)
        return disposicion


class DisposicionDefinitivaPorOPServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.expediente = SimpleNamespace(
            id="EXP-1",
            estado=EstadoExpediente.VALIDADO,
            configuracion_uc_id="UC-1",
            objeto="Objeto",
            establecimiento="EP 1",
        )
        self.analisis = SimpleNamespace(
            orden_pago="OP-1",
            liquidacion="LIQ-1",
            importe_bruto=1000,
            valor_uc=Decimal("1677"),
            cantidad_uc=Decimal("0.5963"),
            procedimiento="Factura Conformada",
            norma_uc="Ley 13.981",
        )
        self.evaluador = MagicMock()
        self.evaluador.evaluar_para_emision_documento.return_value = (
            HabilitacionDisposicion(True, ()),
            ContextoEmisionDisposicion(
                self.expediente,
                SimpleNamespace(fondo_interviniente="FONDO_COMPENSADOR"),
                self.analisis,
                "DOC-000001",
            ),
        )
        self.borrador = DisposicionRead(
            expediente_id="EXP-1",
            documento_op_id="DOC-000001",
            control_proveedor_op_id="CTRL-1",
            seleccion_proveedor_id="SEL-1",
            proveedor_definitivo_id="PROV-1",
            proveedor_definitivo_cuit="30718078063",
            proveedor_definitivo_razon_social="Proveedor OP",
            estado_habilitacion_actual=EstadoHabilitacionProveedorOP.HABILITADO,
            obsoleto=False,
            numero_disposicion=None,
            estado="BORRADOR_PLANTILLA",
            visto="VISTO ____/____",
            considerando="CONSIDERANDO",
            dispone="DISPONE ____/____",
            observaciones_ia=[],
            creado=datetime(2026, 8, 14),
            actualizado=datetime(2026, 8, 14),
        )
        self.borradores = MagicMock()
        self.borradores.obtener_exportable.return_value = self.borrador
        self.docx = MagicMock()
        self.docx.construir_texto_emitido.return_value = "Texto ____/____"
        self.persistence = FakePersistence()
        self.service = EmisionDisposicionService(
            self.evaluador,
            self.borradores,
            self.docx,
            self.persistence,
            now=lambda: datetime(2026, 8, 14, 10),
        )
        self.habilitacion = SimpleNamespace(
            estado=EstadoHabilitacionProveedorOP.HABILITADO,
            mensaje="Habilitado",
            documento_op_id="DOC-000001",
            control_proveedor_op_id="CTRL-1",
            seleccion_proveedor_id="SEL-1",
            proveedor_definitivo_id="PROV-1",
            proveedor_definitivo_cuit="30718078063",
            proveedor_definitivo_razon_social="Proveedor OP",
        )

    def _emitir(self, storage: Path):
        salida = storage / "exports" / "EXP-1" / "DOC-000001" / "definitivas" / "propio.docx"
        salida.parent.mkdir(parents=True)
        salida.write_bytes(b"docx")
        self.docx.generar_docx_definitivo.return_value = salida
        with patch(
            "app.services.emision_disposicion.STORAGE_DIR", storage
        ), patch(
            "app.services.emision_disposicion."
            "evaluar_habilitacion_proveedor_op_service.evaluar",
            return_value=self.habilitacion,
        ):
            return self.service.emitir(
                "EXP-1", "DOC-000001", "148/2026"
            )

    def test_emite_op_explicita_con_numero_y_snapshots(self) -> None:
        with TemporaryDirectory() as temporal:
            resultado = self._emitir(Path(temporal))
        guardada = self.persistence.guardadas[0]
        self.assertEqual(resultado.numero_disposicion, "148/2026")
        self.assertEqual(guardada.documento_op_id, "DOC-000001")
        self.assertEqual(guardada.control_proveedor_op_id, "CTRL-1")
        self.assertEqual(guardada.seleccion_proveedor_id, "SEL-1")
        self.assertEqual(guardada.proveedor_definitivo_id, "PROV-1")
        self.assertEqual(guardada.proveedor_definitivo_cuit, "30718078063")
        self.assertEqual(guardada.texto_emitido, "Texto 148/2026")
        self.evaluador.evaluar_para_emision_documento.assert_called_once_with(
            "EXP-1", "DOC-000001"
        )

    def test_numero_manual_vacio_bloquea_antes_de_consultar(self) -> None:
        with self.assertRaises(EmisionDisposicionError):
            self.service.emitir("EXP-1", "DOC-000001", "   ")
        self.evaluador.evaluar_para_emision_documento.assert_not_called()

    def test_todos_los_estados_f5_no_habilitados_bloquean(self) -> None:
        for estado in EstadoHabilitacionProveedorOP:
            if estado == EstadoHabilitacionProveedorOP.HABILITADO:
                continue
            with self.subTest(estado=estado), patch(
                "app.services.emision_disposicion."
                "evaluar_habilitacion_proveedor_op_service.evaluar",
                return_value=SimpleNamespace(estado=estado, mensaje="Bloqueado"),
            ):
                with self.assertRaises(EmisionProveedorOPNoHabilitadoError):
                    self.service.emitir(
                        "EXP-1", "DOC-000001", "148/2026"
                    )
        self.borradores.obtener_exportable.assert_not_called()

    def test_borrador_de_otro_contexto_bloquea(self) -> None:
        self.habilitacion.control_proveedor_op_id = "CTRL-2"
        with patch(
            "app.services.emision_disposicion."
            "evaluar_habilitacion_proveedor_op_service.evaluar",
            return_value=self.habilitacion,
        ):
            with self.assertRaises(BorradorDisposicionObsoletoError):
                self.service.emitir(
                    "EXP-1", "DOC-000001", "148/2026"
                )

    def test_fallo_persistencia_elimina_solo_archivo_del_intento(self) -> None:
        self.persistence.error = RuntimeError("SQL")
        with TemporaryDirectory() as temporal:
            storage = Path(temporal)
            ganador = storage / "ganador.docx"
            ganador.write_bytes(b"ganador")
            with self.assertRaisesRegex(RuntimeError, "SQL"):
                self._emitir(storage)
            self.assertTrue(ganador.exists())
            salida = self.docx.generar_docx_definitivo.return_value
            self.assertFalse(salida.exists())


class ConsultaDisposicionPorOPTest(unittest.TestCase):
    def test_get_separa_dos_op(self) -> None:
        repo = MagicMock()
        repo.obtener_por_documento_op.side_effect = [
            self._disposicion("DOC-000001", "148/2026"),
            self._disposicion("DOC-000003", "176/2026"),
        ]
        servicio = ConsultaDisposicionService(repo)
        self.assertEqual(
            servicio.obtener_por_documento_op(
                "EXP-1", "DOC-000001"
            ).numero_disposicion,
            "148/2026",
        )
        self.assertEqual(
            servicio.obtener_por_documento_op(
                "EXP-1", "DOC-000003"
            ).numero_disposicion,
            "176/2026",
        )

    def test_get_no_reutiliza_disposicion_de_otro_expediente(self) -> None:
        repo = MagicMock()
        repo.obtener_por_documento_op.return_value = self._disposicion(
            "DOC-000001", "148/2026"
        )
        with self.assertRaises(DisposicionEmitidaNoEncontradaError):
            ConsultaDisposicionService(repo).obtener_por_documento_op(
                "EXP-2", "DOC-000001"
            )

    @staticmethod
    def _disposicion(documento: str, numero: str) -> Disposicion:
        return Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000001",
            expediente_id="EXP-1",
            configuracion_uc_id="UC-1",
            numero_disposicion=numero,
            fecha_emision=datetime(2026, 8, 14),
            fondo_interviniente="FONDO_COMPENSADOR",
            numero_op=documento,
            numero_liquidacion=None,
            proveedor="Proveedor",
            cuit="30718078063",
            importe=Decimal("1000"),
            objeto="Objeto",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.5963"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="Texto",
            ruta_docx=f"exports/EXP-1/{documento}/definitivas/id.docx",
            documento_op_id=documento,
        )


class DisposicionDefinitivaPorOPApiTest(unittest.TestCase):
    def test_post_delega_con_numero_manual(self) -> None:
        service = MagicMock()
        service.emitir.return_value = SimpleNamespace(
            numero_disposicion="148/2026"
        )
        with patch(
            "app.api.expedientes.emision_disposicion_service", service
        ), patch("app.api.expedientes.historial_service"):
            emitir_disposicion_documento(
                "EXP-1",
                "DOC-000001",
                DisposicionEmitirCreate(numero_disposicion="148/2026"),
            )
        service.emitir.assert_called_once_with(
            "EXP-1", "DOC-000001", "148/2026"
        )

    def test_get_inexistente_traduce_404(self) -> None:
        service = MagicMock()
        service.obtener_por_documento_op.side_effect = (
            DisposicionEmitidaNoEncontradaError(
                "EXP-1", "DOC-000001"
            )
        )
        with patch(
            "app.api.expedientes.consulta_disposicion_service", service
        ), self.assertRaises(HTTPException) as contexto:
            obtener_disposicion_emitida_documento(
                "EXP-1", "DOC-000001"
            )
        self.assertEqual(contexto.exception.status_code, 404)


class DisposicionDefinitivaPorOPPersistenciaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.persistence = PostgresEmitirDisposicionPersistence(self.factory)
        self.seleccion_id = "00000000-0000-0000-0000-000000000101"
        self.proveedor_id = "00000000-0000-0000-0000-000000000201"
        self.control_1 = "00000000-0000-0000-0000-000000000301"
        self.control_2 = "00000000-0000-0000-0000-000000000302"
        self.solicitud_id = "00000000-0000-0000-0000-000000000501"
        with self.factory() as session:
            session.add(ExpedienteModel(
                id="EXP-1", numero_interno="033-1/2026", numero_gdeba=None,
                solicitud_intervencion_id=self.solicitud_id, decision_administrativa_id="DEC-1",
                configuracion_uc_id="UC-1", id_suna="1",
                tipo_tramite="FONDO_COMPENSADOR", estado="VALIDADO",
                establecimiento="EP 1", objeto="Objeto",
                numero_disposicion="LEGACY/2026", creado=datetime(2026, 8, 14),
            ))
            session.add_all([
                DocumentoModel(secuencia=1, expediente_id="EXP-1", tipo="OP", nombre_archivo="op1.pdf", ruta="op1.pdf", fecha_carga=datetime(2026, 8, 14)),
                DocumentoModel(secuencia=3, expediente_id="EXP-1", tipo="OP", nombre_archivo="op3.pdf", ruta="op3.pdf", fecha_carga=datetime(2026, 8, 14)),
                SeleccionProveedorModel(
                    id_seleccion=self.seleccion_id, expediente_id="EXP-1",
                    solicitud_intervencion_id=self.solicitud_id, decision_administrativa_id="00000000-0000-0000-0000-000000000401",
                    proveedor_id=self.proveedor_id, fecha_seleccion=datetime(2026, 8, 14),
                    seleccionado_por="Usuario", proveedor_cuit="30718078063",
                    proveedor_razon_social="Proveedor OP", motivo_reemplazo=None,
                    vigente=True,
                ),
            ])
            session.add_all([
                self._control(self.control_1, 1, 1),
                self._control(self.control_2, 2, 3),
            ])
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_dos_op_se_emiten_sin_cambiar_estado_expediente(self) -> None:
        self.persistence.emitir(self._disposicion(1), "EXP-1")
        self.persistence.emitir(self._disposicion(3), "EXP-1")
        with self.factory() as session:
            expediente = session.scalar(
                select(ExpedienteModel).where(ExpedienteModel.id == "EXP-1")
            )
            self.assertEqual(expediente.estado, "VALIDADO")

    def test_seleccion_reemplazada_bloquea(self) -> None:
        with self.factory() as session:
            session.get(SeleccionProveedorModel, self.seleccion_id).vigente = False
            session.commit()
        with self.assertRaises(ContextoEmisionObsoletoError):
            self.persistence.emitir(self._disposicion(1), "EXP-1")

    def test_control_mas_nuevo_bloquea_contexto_anterior(self) -> None:
        with self.factory() as session:
            session.add(self._control(
                "00000000-0000-0000-0000-000000000399", 9, 1
            ))
            session.commit()
        with self.assertRaises(ContextoEmisionObsoletoError):
            self.persistence.emitir(self._disposicion(1), "EXP-1")

    def test_control_no_coincide_bloquea(self) -> None:
        with self.factory() as session:
            session.get(ControlProveedorOPModel, self.control_1).estado = "CUIT_DIFERENTE"
            session.commit()
        with self.assertRaises(ContextoEmisionObsoletoError):
            self.persistence.emitir(self._disposicion(1), "EXP-1")

    def test_snapshot_modificado_bloquea(self) -> None:
        disposicion = self._disposicion(1)
        object.__setattr__(disposicion, "proveedor_definitivo_razon_social", "Otra")
        with self.assertRaises(ContextoEmisionObsoletoError):
            self.persistence.emitir(disposicion, "EXP-1")

    def _control(self, control_id: str, secuencia: int, documento: int):
        return ControlProveedorOPModel(
            id_control=control_id, secuencia=secuencia, expediente_id="EXP-1",
            documento_secuencia=documento, solicitud_intervencion_id=self.solicitud_id,
            seleccion_proveedor_id=self.seleccion_id, estado="COINCIDE",
            proveedor_cuit_seleccionado="30718078063",
            proveedor_razon_social_seleccionada="Proveedor OP",
            cuit_detectado="30718078063", razon_social_detectada="Proveedor OP",
            advertencias=[], fecha_control=datetime(2026, 8, 14), modo_analisis="PDF",
        )

    def _disposicion(self, documento: int) -> Disposicion:
        return Disposicion(
            id_disposicion=f"00000000-0000-0000-0000-{documento:012d}",
            expediente_id="EXP-1", configuracion_uc_id="UC-1",
            numero_disposicion=f"{documento}/2026", fecha_emision=datetime(2026, 8, 14),
            fondo_interviniente="FONDO_COMPENSADOR", numero_op=f"OP-{documento}",
            numero_liquidacion=None, proveedor="Proveedor OP", cuit="30718078063",
            importe=Decimal("1000"), objeto="Objeto", establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"), cantidad_uc=Decimal("0.5963"),
            procedimiento_contratacion="Factura Conformada", norma_uc="Ley 13.981",
            texto_emitido="Texto", ruta_docx=f"exports/EXP-1/DOC-{documento:06d}/definitivas/id.docx",
            documento_op_id=f"DOC-{documento:06d}",
            control_proveedor_op_id=self.control_1 if documento == 1 else self.control_2,
            seleccion_proveedor_id=self.seleccion_id,
            proveedor_definitivo_id=self.proveedor_id,
            proveedor_definitivo_cuit="30718078063",
            proveedor_definitivo_razon_social="Proveedor OP",
        )


if __name__ == "__main__":
    unittest.main()
