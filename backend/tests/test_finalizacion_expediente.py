import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.base import Base
from app.infrastructure.database.models.disposicion_model import DisposicionModel
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.persistence.finalizacion_expediente_postgres import (
    PostgresFinalizacionExpedientePersistence,
)
from app.repositories.finalizacion_expediente_persistence import (
    FechaCierreAnteriorAFormalizacionError,
    FechaDesistimientoAnteriorACreacionError,
    FinalizacionExpedienteError,
)
from app.schemas.finalizacion_expediente import (
    CierreExpedienteCreate,
    DesistimientoExpedienteCreate,
)
from app.services.finalizacion_expediente import (
    FechaFinalizacionFuturaError,
    FinalizacionExpedienteService,
)
from app.domain.finalizacion_expediente import ExpedienteTerminalError
from app.domain.seleccion_proveedor import SeleccionProveedor
from app.infrastructure.database.repositories.documento_postgres_repository import PostgresDocumentoRepository
from app.infrastructure.database.repositories.expediente_postgres_repository import PostgresExpedienteRepository
from app.infrastructure.database.repositories.seleccion_proveedor_postgres_repository import PostgresSeleccionProveedorRepository
from app.schemas.documento import DocumentoCreate


class FinalizacionExpedienteTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        self.persistence = PostgresFinalizacionExpedientePersistence(self.factory)
        self.ahora = datetime(2026, 8, 19, 12, 0)
        self.service = FinalizacionExpedienteService(
            self.persistence, now=lambda: self.ahora
        )

    def tearDown(self):
        self.engine.dispose()

    def _expediente(self, estado="VALIDADO", expediente_id="EXP-1", creado=None):
        modelo = ExpedienteModel(
            id=expediente_id,
            numero_interno=f"{expediente_id}/2026",
            numero_gdeba=None,
            solicitud_intervencion_id=None,
            decision_administrativa_id=None,
            configuracion_uc_id=None,
            id_suna=None,
            tipo_tramite="FONDO_COMPENSADOR",
            estado=estado,
            establecimiento="EP 1",
            objeto="Obra",
            numero_disposicion=None,
            creado=creado or datetime(2026, 8, 1, 10, 0),
        )
        with self.factory() as session:
            session.add(modelo)
            session.commit()
        return modelo

    def _op(self, expediente_id="EXP-1", secuencia=1):
        with self.factory() as session:
            session.add(DocumentoModel(
                secuencia=secuencia,
                expediente_id=expediente_id,
                tipo="OP",
                nombre_archivo=f"op-{secuencia}.pdf",
                ruta=f"storage/op-{secuencia}.pdf",
                fecha_carga=datetime(2026, 8, 10),
            ))
            session.commit()

    def _disposicion(self, secuencia=1, formalizada=True, expediente_id="EXP-1"):
        with self.factory() as session:
            session.add(DisposicionModel(
                id_disposicion=f"00000000-0000-0000-0000-{secuencia:012d}",
                expediente_id=expediente_id,
                configuracion_uc_id="CFG-1",
                numero_disposicion=f"{secuencia}/2026",
                fecha_emision=datetime(2026, 8, 11),
                fondo_interviniente="FONDO_COMPENSADOR",
                numero_op=f"OP-{secuencia}",
                numero_liquidacion=None,
                proveedor="Proveedor",
                cuit="30712345678",
                importe=Decimal("100"),
                objeto="Obra",
                establecimiento="EP 1",
                valor_uc_aplicado=Decimal("1"),
                cantidad_uc=Decimal("100"),
                procedimiento_contratacion="Factura conformada",
                norma_uc="Norma",
                texto_emitido="Texto",
                ruta_docx="storage/disposicion.docx",
                documento_op_secuencia=secuencia,
                fecha_formalizacion=date(2026, 8, 12) if formalizada else None,
                usuario_registro_formalizacion="sistema" if formalizada else None,
                registrado_formalizacion_en=datetime(2026, 8, 12, 10) if formalizada else None,
            ))
            session.commit()

    def test_sin_op_bloquea_cierre(self):
        self._expediente()
        resultado = self.service.habilitacion_cierre("EXP-1")
        self.assertEqual("SIN_OP", resultado.estado.value)
        self.assertFalse(resultado.habilitado)

    def test_op_sin_disposicion_bloquea(self):
        self._expediente(); self._op()
        self.assertEqual(
            "OP_SIN_DISPOSICION",
            self.service.habilitacion_cierre("EXP-1").estado.value,
        )

    def test_disposicion_sin_formalizar_bloquea(self):
        self._expediente(); self._op(); self._disposicion(formalizada=False)
        self.assertEqual(
            "DISPOSICION_SIN_FORMALIZAR",
            self.service.habilitacion_cierre("EXP-1").estado.value,
        )

    def test_una_op_formalizada_habilita_y_cierra(self):
        self._expediente(); self._op(); self._disposicion()
        self.assertTrue(self.service.habilitacion_cierre("EXP-1").habilitado)
        resultado = self.service.cerrar(
            "EXP-1", CierreExpedienteCreate(
                fecha_cierre=date(2026, 8, 19), confirmacion_completitud=True
            )
        )
        self.assertEqual("CERRADO", resultado.estado.value)
        self.assertEqual("sistema", resultado.usuario_registro_cierre)
        self.assertEqual(self.ahora, resultado.registrado_cierre_en)

    def test_varias_op_formalizadas_habilitan(self):
        self._expediente()
        for numero in (1, 2):
            self._op(secuencia=numero); self._disposicion(secuencia=numero)
        resultado = self.service.habilitacion_cierre("EXP-1")
        self.assertEqual((2, 2, 2), (
            resultado.cantidad_op,
            resultado.disposiciones_emitidas,
            resultado.disposiciones_formalizadas,
        ))

    def test_segundo_cierre_conflicto(self):
        self._expediente(); self._op(); self._disposicion()
        data = CierreExpedienteCreate(fecha_cierre=date(2026, 8, 19), confirmacion_completitud=True)
        self.service.cerrar("EXP-1", data)
        with self.assertRaises(FinalizacionExpedienteError):
            self.service.cerrar("EXP-1", data)

    def test_fecha_cierre_anterior_formalizacion_rechazada(self):
        self._expediente(); self._op(); self._disposicion()
        with self.assertRaises(FechaCierreAnteriorAFormalizacionError):
            self.service.cerrar("EXP-1", CierreExpedienteCreate(
                fecha_cierre=date(2026, 8, 11), confirmacion_completitud=True
            ))

    def test_fecha_futura_rechazada(self):
        self._expediente(); self._op(); self._disposicion()
        with self.assertRaises(FechaFinalizacionFuturaError):
            self.service.cerrar("EXP-1", CierreExpedienteCreate(
                fecha_cierre=self.ahora.date() + timedelta(days=1),
                confirmacion_completitud=True,
            ))

    def test_cero_op_habilita_desistimiento(self):
        self._expediente(estado="BORRADOR")
        self.assertTrue(
            self.service.habilitacion_desistimiento("EXP-1").habilitado
        )

    def test_una_op_bloquea_desistimiento(self):
        self._expediente(estado="BORRADOR"); self._op()
        self.assertEqual(
            "TIENE_OP",
            self.service.habilitacion_desistimiento("EXP-1").estado.value,
        )

    def test_desistimiento_preserva_motivo_y_metadatos(self):
        self._expediente(estado="BORRADOR")
        resultado = self.service.desistir(
            "EXP-1", DesistimientoExpedienteCreate(
                fecha_desistimiento=date(2026, 8, 19),
                motivo_desistimiento="  Presupuesto no aceptado  ",
            )
        )
        self.assertEqual("DESISTIDO", resultado.estado.value)
        self.assertEqual("Presupuesto no aceptado", resultado.motivo_desistimiento)
        self.assertEqual("sistema", resultado.usuario_registro_desistimiento)

    def test_fecha_desistimiento_anterior_creacion_rechazada(self):
        self._expediente(estado="BORRADOR")
        with self.assertRaises(FechaDesistimientoAnteriorACreacionError):
            self.service.desistir("EXP-1", DesistimientoExpedienteCreate(
                fecha_desistimiento=date(2026, 7, 31),
                motivo_desistimiento="No continuar",
            ))

    def test_segundo_desistimiento_conflicto(self):
        self._expediente(estado="BORRADOR")
        data = DesistimientoExpedienteCreate(
            fecha_desistimiento=date(2026, 8, 19), motivo_desistimiento="No continuar"
        )
        self.service.desistir("EXP-1", data)
        with self.assertRaises(FinalizacionExpedienteError):
            self.service.desistir("EXP-1", data)

    def test_dos_expedientes_misma_solicitud_son_independientes(self):
        self._expediente(estado="BORRADOR", expediente_id="EXP-A")
        self._expediente(estado="BORRADOR", expediente_id="EXP-B")
        self.service.desistir("EXP-A", DesistimientoExpedienteCreate(
            fecha_desistimiento=date(2026, 8, 19), motivo_desistimiento="No continuar"
        ))
        self.assertTrue(self.service.habilitacion_desistimiento("EXP-B").habilitado)

    def test_documento_nuevo_bloqueado_en_desistido(self):
        self._expediente(estado="BORRADOR")
        self.service.desistir("EXP-1", DesistimientoExpedienteCreate(
            fecha_desistimiento=date(2026, 8, 19), motivo_desistimiento="No continuar"
        ))
        with self.assertRaises(ExpedienteTerminalError):
            PostgresDocumentoRepository(self.factory).guardar(
                "EXP-1",
                DocumentoCreate(tipo="OTRO", nombre_archivo="nuevo.pdf", ruta="storage/nuevo.pdf"),
                self.ahora,
            )

    def test_edicion_bloqueada_en_cerrado(self):
        self._expediente(); self._op(); self._disposicion()
        cerrado = self.persistence.cerrar(
            "EXP-1", date(2026, 8, 19), "sistema", self.ahora
        )
        cerrado = cerrado.__class__(**{
            **cerrado.__dict__, "objeto": "Cambio posterior"
        })
        with self.assertRaises(ExpedienteTerminalError):
            PostgresExpedienteRepository(self.factory).guardar(cerrado)

    def test_seleccion_bloqueada_en_desistido(self):
        self._expediente(estado="BORRADOR")
        self.service.desistir("EXP-1", DesistimientoExpedienteCreate(
            fecha_desistimiento=date(2026, 8, 19), motivo_desistimiento="No continuar"
        ))
        seleccion = SeleccionProveedor(
            id_seleccion="00000000-0000-0000-0000-000000000001",
            expediente_id="EXP-1",
            solicitud_intervencion_id="00000000-0000-0000-0000-000000000002",
            decision_administrativa_id="00000000-0000-0000-0000-000000000003",
            proveedor_id="00000000-0000-0000-0000-000000000004",
            fecha_seleccion=self.ahora,
            seleccionado_por="usuario",
            proveedor_cuit="30712345678",
            proveedor_razon_social="Proveedor",
            motivo_reemplazo=None,
            vigente=True,
        )
        with self.assertRaises(ExpedienteTerminalError):
            PostgresSeleccionProveedorRepository(self.factory).guardar(seleccion)


if __name__ == "__main__":
    unittest.main()
