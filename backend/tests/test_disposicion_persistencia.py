import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.domain.disposicion import Disposicion
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.disposicion_mapper import (
    a_dominio,
    a_modelo,
)
from app.infrastructure.database.repositories.disposicion_postgres_repository import (
    PostgresDisposicionRepository,
)
from app.repositories.disposicion_repository import (
    DisposicionYaRegistradaError,
)


class DisposicionPersistenciaTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def tearDown(self):
        self.engine.dispose()

    def test_mapper_conserva_explicita_y_completamente_los_campos(self):
        original = self._crear()
        modelo = a_modelo(original)
        for campo, valor in original.__dict__.items():
            self.assertEqual(getattr(modelo, campo), valor)
        self.assertEqual(a_dominio(modelo), original)

    def test_guarda_y_recupera_desde_nueva_instancia(self):
        original = self._crear()
        PostgresDisposicionRepository(self.factory).guardar(original)
        reconstruido = PostgresDisposicionRepository(self.factory)
        self.assertEqual(
            reconstruido.obtener_por_id(original.id_disposicion),
            original,
        )
        self.assertEqual(
            reconstruido.obtener_por_expediente(original.expediente_id),
            original,
        )
        self.assertEqual(
            reconstruido.obtener_por_numero(original.numero_disposicion),
            original,
        )

    def test_conflictos_conservan_criterio_y_no_actualizan(self):
        repo = PostgresDisposicionRepository(self.factory)
        original = self._crear()
        repo.guardar(original)
        casos = (
            ("id", {"expediente_id": "EXP-2", "numero_disposicion": "2/2026"}),
            (
                "expediente",
                {
                    "id_disposicion":
                        "00000000-0000-0000-0000-000000000002",
                    "numero_disposicion": "2/2026",
                },
            ),
            (
                "numero_disposicion",
                {
                    "id_disposicion":
                        "00000000-0000-0000-0000-000000000003",
                    "expediente_id": "EXP-3",
                },
            ),
        )
        for criterio, cambios in casos:
            with self.subTest(criterio=criterio):
                with self.assertRaises(
                    DisposicionYaRegistradaError
                ) as contexto:
                    repo.guardar(
                        Disposicion(**(original.__dict__ | cambios))
                    )
                self.assertEqual(contexto.exception.criterio, criterio)
        self.assertEqual(
            repo.obtener_por_id(original.id_disposicion),
            original,
        )
        self.assertFalse(hasattr(repo, "actualizar"))

    def test_traduce_solamente_integrity_errors_conocidos(self):
        casos = (
            ("id", "UNIQUE constraint failed: disposiciones.id_disposicion"),
            ("expediente", "UNIQUE constraint failed: disposiciones.expediente_id"),
            (
                "numero_disposicion",
                "UNIQUE constraint failed: disposiciones.numero_disposicion",
            ),
        )
        for criterio, mensaje in casos:
            with self.subTest(criterio=criterio):
                session = MagicMock()
                session.scalar.side_effect = [None, None, None]
                session.commit.side_effect = IntegrityError(
                    "insert", {}, Exception(mensaje)
                )
                factory = MagicMock()
                factory.return_value.__enter__.return_value = session
                with self.assertRaises(
                    DisposicionYaRegistradaError
                ) as contexto:
                    PostgresDisposicionRepository(factory).guardar(
                        self._crear()
                    )
                self.assertEqual(contexto.exception.criterio, criterio)
                session.rollback.assert_called_once_with()

    def test_integrity_error_desconocido_se_propaga(self):
        error = IntegrityError(
            "insert", {}, Exception("FOREIGN KEY constraint failed")
        )
        session = MagicMock()
        session.scalar.side_effect = [None, None, None]
        session.commit.side_effect = error
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        with self.assertRaises(IntegrityError) as contexto:
            PostgresDisposicionRepository(factory).guardar(self._crear())
        self.assertIs(contexto.exception, error)
        session.rollback.assert_called_once_with()

    @staticmethod
    def _crear() -> Disposicion:
        return Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000001",
            expediente_id="EXP-1",
            configuracion_uc_id="configuracion-1",
            numero_disposicion="1/2026",
            fecha_emision=datetime(2026, 7, 28, 10),
            fondo_interviniente="FONDO_COMPENSADOR",
            numero_op="OP-1",
            numero_liquidacion="LIQ-1",
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe=Decimal("1000.50"),
            objeto="Objeto",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.59660"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="Texto emitido",
            ruta_docx="exports/EXP-1/disposicion.docx",
        )
