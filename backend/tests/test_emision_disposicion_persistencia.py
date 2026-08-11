import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.infrastructure.database.persistence.emitir_disposicion_postgres import (
    PostgresEmitirDisposicionPersistence,
)
from app.infrastructure.database.repositories.expediente_postgres_repository import (
    PostgresExpedienteRepository,
)
from app.repositories.disposicion_repository import (
    DisposicionYaRegistradaError,
)
from app.repositories.emitir_disposicion_persistence import (
    EstadoExpedienteIncompatibleError,
)


class EmisionDisposicionPersistenciaTest(unittest.TestCase):
    """SQLite no valida el bloqueo real de SELECT FOR UPDATE."""

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def tearDown(self):
        self.engine.dispose()

    def test_devuelve_expediente_utilizable_tras_cerrar_sesion(self):
        self._guardar_expediente("EXP-1", EstadoExpediente.VALIDADO)
        resultado = PostgresEmitirDisposicionPersistence(
            self.factory
        ).emitir(self._disposicion(), "EXP-1")
        self.assertEqual(resultado.id, "EXP-1")
        self.assertEqual(
            resultado.estado,
            EstadoExpediente.DISPOSICION_EMITIDA,
        )
        with self.factory() as session:
            self.assertIsNotNone(
                session.get(
                    DisposicionModel,
                    self._disposicion().id_disposicion,
                )
            )

    def test_ejecuta_un_flush_y_un_commit(self):
        session = MagicMock()
        session.scalar.side_effect = [
            self._modelo_expediente_mock(), None, None, None
        ]
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        PostgresEmitirDisposicionPersistence(factory).emitir(
            self._disposicion(), "EXP-1"
        )
        session.flush.assert_called_once_with()
        session.commit.assert_called_once_with()
        session.rollback.assert_not_called()

    def test_rollback_si_falla_flush(self):
        session = MagicMock()
        session.scalar.side_effect = [
            self._modelo_expediente_mock(), None, None, None
        ]
        session.flush.side_effect = RuntimeError("fallo")
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        with self.assertRaisesRegex(RuntimeError, "fallo"):
            PostgresEmitirDisposicionPersistence(factory).emitir(
                self._disposicion(), "EXP-1"
            )
        session.rollback.assert_called_once_with()
        session.commit.assert_not_called()

    def test_conflictos_publicos_conservan_misma_semantica(self):
        for indice, criterio in enumerate(
            ("id", "numero_disposicion")
        ):
            with self.subTest(criterio=criterio):
                session = MagicMock()
                session.scalar.side_effect = [
                    self._modelo_expediente_mock(),
                    *[
                        self._disposicion() if posicion == indice else None
                        for posicion in range(2)
                    ],
                ]
                factory = MagicMock()
                factory.return_value.__enter__.return_value = session
                with self.assertRaises(
                    DisposicionYaRegistradaError
                ) as contexto:
                    PostgresEmitirDisposicionPersistence(
                        factory
                    ).emitir(self._disposicion(), "EXP-1")
                self.assertEqual(contexto.exception.criterio, criterio)
                session.rollback.assert_called_once_with()
                session.commit.assert_not_called()

    def test_integrity_errors_conocidos_y_desconocido(self):
        casos = (
            ("id", "UNIQUE constraint failed: disposiciones.id_disposicion"),
            (
                "numero_disposicion",
                "UNIQUE constraint failed: disposiciones.numero_disposicion",
            ),
        )
        for criterio, mensaje in casos:
            with self.subTest(criterio=criterio):
                session = MagicMock()
                session.scalar.side_effect = [
                    self._modelo_expediente_mock(), None, None
                ]
                session.flush.side_effect = IntegrityError(
                    "insert", {}, Exception(mensaje)
                )
                factory = MagicMock()
                factory.return_value.__enter__.return_value = session
                with self.assertRaises(
                    DisposicionYaRegistradaError
                ) as contexto:
                    PostgresEmitirDisposicionPersistence(
                        factory
                    ).emitir(self._disposicion(), "EXP-1")
                self.assertEqual(contexto.exception.criterio, criterio)
                session.rollback.assert_called_once_with()
                session.commit.assert_not_called()

        error = IntegrityError(
            "insert", {}, Exception("FOREIGN KEY constraint failed")
        )
        session = MagicMock()
        session.scalar.side_effect = [
            self._modelo_expediente_mock(), None, None
        ]
        session.flush.side_effect = error
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        with self.assertRaises(IntegrityError) as contexto:
            PostgresEmitirDisposicionPersistence(factory).emitir(
                self._disposicion(), "EXP-1"
            )
        self.assertIs(contexto.exception, error)
        session.rollback.assert_called_once_with()
        session.commit.assert_not_called()

    def test_estado_incompatible_no_inserta(self):
        self._guardar_expediente("EXP-1", EstadoExpediente.BORRADOR)
        with self.assertRaises(EstadoExpedienteIncompatibleError):
            PostgresEmitirDisposicionPersistence(
                self.factory
            ).emitir(self._disposicion(), "EXP-1")

    def _guardar_expediente(self, expediente_id, estado):
        PostgresExpedienteRepository(self.factory).guardar(
            Expediente(
                id=expediente_id,
                numero_interno=f"033-{expediente_id}/2026",
                numero_gdeba=None,
                solicitud_intervencion_id="SOL-1",
                decision_administrativa_id="DEC-1",
                configuracion_uc_id="configuracion-1",
                id_suna="1",
                tipo_tramite="FONDO_COMPENSADOR",
                estado=estado,
                establecimiento="EP 1",
                objeto="Objeto",
                numero_disposicion="1/2026",
                creado=datetime(2026, 7, 28, 9),
            )
        )

    @staticmethod
    def _modelo_expediente_mock():
        modelo = MagicMock()
        modelo.id = "EXP-1"
        modelo.numero_interno = "033-EXP-1/2026"
        modelo.numero_gdeba = None
        modelo.solicitud_intervencion_id = "SOL-1"
        modelo.decision_administrativa_id = "DEC-1"
        modelo.configuracion_uc_id = "configuracion-1"
        modelo.id_suna = "1"
        modelo.tipo_tramite = "FONDO_COMPENSADOR"
        modelo.estado = EstadoExpediente.VALIDADO.value
        modelo.establecimiento = "EP 1"
        modelo.objeto = "Objeto"
        modelo.numero_disposicion = "1/2026"
        modelo.creado = datetime(2026, 7, 28, 9)
        return modelo

    @staticmethod
    def _disposicion():
        return Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000001",
            expediente_id="EXP-1",
            configuracion_uc_id="configuracion-1",
            numero_disposicion="1/2026",
            fecha_emision=datetime(2026, 7, 28, 10),
            fondo_interviniente="FONDO_COMPENSADOR",
            numero_op="OP-1",
            numero_liquidacion=None,
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe=Decimal("1000"),
            objeto="Objeto",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.59630"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="Texto",
            ruta_docx="exports/EXP-1/disposicion.docx",
        )
