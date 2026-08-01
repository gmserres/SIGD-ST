import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.disposicion_mapper import a_modelo
from app.infrastructure.database.models.disposicion_model import DisposicionModel
from app.infrastructure.database.persistence.registrar_firma_postgres import (
    PostgresRegistrarFirmaPersistence,
)
from app.infrastructure.database.repositories.expediente_postgres_repository import (
    PostgresExpedienteRepository,
)
from app.repositories.registrar_firma_persistence import (
    DisposicionEmitidaNoEncontradaAlFirmarError,
    EstadoExpedienteIncompatibleParaFirmaError,
    ExpedienteNoEncontradoAlRegistrarFirmaError,
    FechaFirmaAnteriorAEmisionError,
    FirmaYaRegistradaError,
)


class RegistroFirmaPersistenciaTest(unittest.TestCase):
    """SQLite no valida el bloqueo real de SELECT FOR UPDATE."""

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self.persistence = PostgresRegistrarFirmaPersistence(self.factory)

    def tearDown(self):
        self.engine.dispose()

    def test_registra_persiste_y_recupera_sin_modificar_disposicion(self):
        self._guardar_expediente()
        original = self._guardar_disposicion()

        resultado = self.persistence.registrar(
            "EXP-1", date(2026, 8, 1), "Secretario Técnico"
        )

        self.assertEqual(resultado.estado, EstadoExpediente.FIRMADO)
        self.assertEqual(resultado.fecha_firma, date(2026, 8, 1))
        self.assertEqual(
            resultado.usuario_registro_firma, "Secretario Técnico"
        )
        reconstruido = PostgresExpedienteRepository(
            self.factory
        ).obtener_por_id("EXP-1")
        self.assertEqual(reconstruido, resultado)
        with self.factory() as session:
            disposicion = session.get(
                DisposicionModel, original.id_disposicion
            )
            self.assertEqual(disposicion.fecha_emision, original.fecha_emision)
            self.assertEqual(disposicion.texto_emitido, original.texto_emitido)

    def test_admite_misma_fecha_de_emision(self):
        self._guardar_expediente()
        self._guardar_disposicion()
        resultado = self.persistence.registrar(
            "EXP-1", date(2026, 7, 31), "Secretario Técnico"
        )
        self.assertEqual(resultado.fecha_firma, date(2026, 7, 31))

    def test_rechaza_expediente_inexistente(self):
        with self.assertRaises(ExpedienteNoEncontradoAlRegistrarFirmaError):
            self.persistence.registrar(
                "NO-EXISTE", date(2026, 8, 1), "Secretario Técnico"
            )

    def test_rechaza_estado_incompatible(self):
        self._guardar_expediente(EstadoExpediente.VALIDADO)
        self._guardar_disposicion()
        with self.assertRaises(EstadoExpedienteIncompatibleParaFirmaError):
            self.persistence.registrar(
                "EXP-1", date(2026, 8, 1), "Secretario Técnico"
            )

    def test_rechaza_firma_duplicada(self):
        self._guardar_expediente()
        self._guardar_disposicion()
        self.persistence.registrar(
            "EXP-1", date(2026, 8, 1), "Secretario Técnico"
        )
        with self.assertRaises(FirmaYaRegistradaError):
            self.persistence.registrar(
                "EXP-1", date(2026, 8, 1), "Secretario Técnico"
            )

    def test_rechaza_disposicion_inexistente(self):
        self._guardar_expediente()
        with self.assertRaises(DisposicionEmitidaNoEncontradaAlFirmarError):
            self.persistence.registrar(
                "EXP-1", date(2026, 8, 1), "Secretario Técnico"
            )

    def test_rechaza_fecha_anterior_a_emision(self):
        self._guardar_expediente()
        self._guardar_disposicion()
        with self.assertRaises(FechaFirmaAnteriorAEmisionError):
            self.persistence.registrar(
                "EXP-1", date(2026, 7, 30), "Secretario Técnico"
            )

    def test_ejecuta_un_flush_y_un_commit(self):
        session = MagicMock()
        session.scalar.side_effect = [
            self._modelo_expediente_mock(),
            MagicMock(fecha_emision=datetime(2026, 7, 31, 10)),
        ]
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        PostgresRegistrarFirmaPersistence(factory).registrar(
            "EXP-1", date(2026, 8, 1), "Secretario Técnico"
        )
        session.flush.assert_called_once_with()
        session.commit.assert_called_once_with()
        session.rollback.assert_not_called()

    def test_rollback_completo_ante_error(self):
        modelo = self._modelo_expediente_mock()
        session = MagicMock()
        session.scalar.side_effect = [
            modelo,
            MagicMock(fecha_emision=datetime(2026, 7, 31, 10)),
        ]
        session.flush.side_effect = RuntimeError("fallo")
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        with self.assertRaisesRegex(RuntimeError, "fallo"):
            PostgresRegistrarFirmaPersistence(factory).registrar(
                "EXP-1", date(2026, 8, 1), "Secretario Técnico"
            )
        session.rollback.assert_called_once_with()
        session.commit.assert_not_called()

    def _guardar_expediente(
        self,
        estado=EstadoExpediente.DISPOSICION_EMITIDA,
    ):
        PostgresExpedienteRepository(self.factory).guardar(
            Expediente(
                id="EXP-1",
                numero_interno="033-1/2026",
                numero_gdeba=None,
                solicitud_intervencion_id="SOL-1",
                decision_administrativa_id="DEC-1",
                configuracion_uc_id="configuracion-1",
                id_suna=None,
                tipo_tramite="FONDO_COMPENSADOR",
                estado=estado,
                establecimiento="EP 1",
                objeto="Compra",
                numero_disposicion="1/2026",
                creado=datetime(2026, 7, 30, 9),
            )
        )

    def _guardar_disposicion(self):
        disposicion = Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000013",
            expediente_id="EXP-1",
            configuracion_uc_id="configuracion-1",
            numero_disposicion="1/2026",
            fecha_emision=datetime(2026, 7, 31, 10),
            fondo_interviniente="FONDO_COMPENSADOR",
            numero_op="OP-1",
            numero_liquidacion=None,
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe=Decimal("1000"),
            objeto="Compra",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.59630"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="Texto emitido",
            ruta_docx="exports/EXP-1/disposicion.docx",
        )
        with self.factory() as session:
            session.add(a_modelo(disposicion))
            session.commit()
        return disposicion

    @staticmethod
    def _modelo_expediente_mock():
        modelo = MagicMock()
        modelo.id = "EXP-1"
        modelo.numero_interno = "033-1/2026"
        modelo.numero_gdeba = None
        modelo.solicitud_intervencion_id = "SOL-1"
        modelo.decision_administrativa_id = "DEC-1"
        modelo.configuracion_uc_id = "configuracion-1"
        modelo.id_suna = None
        modelo.tipo_tramite = "FONDO_COMPENSADOR"
        modelo.estado = EstadoExpediente.DISPOSICION_EMITIDA.value
        modelo.establecimiento = "EP 1"
        modelo.objeto = "Compra"
        modelo.numero_disposicion = "1/2026"
        modelo.creado = datetime(2026, 7, 30, 9)
        modelo.fecha_firma = None
        modelo.usuario_registro_firma = None
        return modelo


if __name__ == "__main__":
    unittest.main()
