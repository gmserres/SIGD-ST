import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.disposicion import Disposicion
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.disposicion_mapper import (
    a_dominio,
    a_modelo,
)
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.infrastructure.database.repositories.disposicion_postgres_repository import (
    PostgresDisposicionRepository,
)
from app.repositories.disposicion_repository import (
    DisposicionExpedienteAmbiguoError,
    DisposicionYaRegistradaError,
)


class DisposicionPorOPPersistenciaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repository = PostgresDisposicionRepository(self.factory)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_disposicion_legacy_reconstruye_nuevos_campos_null(self) -> None:
        reconstruida = a_dominio(a_modelo(self._crear()))
        self.assertIsNone(reconstruida.documento_op_id)
        self.assertIsNone(reconstruida.control_proveedor_op_id)
        self.assertIsNone(reconstruida.seleccion_proveedor_id)
        self.assertIsNone(reconstruida.proveedor_definitivo_id)
        self.assertIsNone(reconstruida.proveedor_definitivo_cuit)
        self.assertIsNone(reconstruida.proveedor_definitivo_razon_social)

    def test_disposicion_f6_conserva_documento_op(self) -> None:
        original = self._crear(documento_op_id="DOC-000101")
        self.assertEqual(a_dominio(a_modelo(original)).documento_op_id, "DOC-000101")

    def test_disposicion_f6_conserva_control_habilitante(self) -> None:
        original = self._crear(control_proveedor_op_id=self._uuid(101))
        self.assertEqual(
            a_dominio(a_modelo(original)).control_proveedor_op_id,
            self._uuid(101),
        )

    def test_disposicion_f6_conserva_seleccion(self) -> None:
        original = self._crear(seleccion_proveedor_id=self._uuid(201))
        self.assertEqual(
            a_dominio(a_modelo(original)).seleccion_proveedor_id,
            self._uuid(201),
        )

    def test_disposicion_f6_conserva_proveedor_definitivo(self) -> None:
        original = self._crear(proveedor_definitivo_id=self._uuid(301))
        self.assertEqual(
            a_dominio(a_modelo(original)).proveedor_definitivo_id,
            self._uuid(301),
        )

    def test_disposicion_f6_conserva_cuit_snapshot(self) -> None:
        original = self._crear(proveedor_definitivo_cuit="30-71807806-3")
        self.assertEqual(
            a_dominio(a_modelo(original)).proveedor_definitivo_cuit,
            "30718078063",
        )

    def test_disposicion_f6_conserva_razon_social_snapshot_nullable(self) -> None:
        con_razon = self._crear(
            proveedor_definitivo_razon_social="Razón OP"
        )
        sin_razon = self._crear()
        self.assertEqual(
            a_dominio(a_modelo(con_razon)).proveedor_definitivo_razon_social,
            "Razón OP",
        )
        self.assertIsNone(
            a_dominio(a_modelo(sin_razon)).proveedor_definitivo_razon_social
        )

    def test_dos_op_del_mismo_expediente_admiten_dos_disposiciones(self) -> None:
        self.repository.guardar(self._crear(documento_op_id="DOC-000101"))
        self.repository.guardar(
            self._crear(
                ordinal=2,
                documento_op_id="DOC-000102",
            )
        )
        self.assertEqual(len(self.repository.listar_por_expediente("EXP-1")), 2)

    def test_tres_op_del_mismo_expediente_admiten_tres_disposiciones(self) -> None:
        for ordinal in (1, 2, 3):
            self.repository.guardar(
                self._crear(
                    ordinal=ordinal,
                    documento_op_id=f"DOC-{100 + ordinal:06d}",
                )
            )
        self.assertEqual(len(self.repository.listar_por_expediente("EXP-1")), 3)

    def test_misma_op_rechaza_segunda_disposicion(self) -> None:
        self.repository.guardar(self._crear(documento_op_id="DOC-000101"))
        with self.assertRaises(DisposicionYaRegistradaError) as contexto:
            self.repository.guardar(
                self._crear(ordinal=2, documento_op_id="DOC-000101")
            )
        self.assertEqual(contexto.exception.criterio, "documento_op")

    def test_numero_disposicion_continua_siendo_unico(self) -> None:
        self.repository.guardar(self._crear(documento_op_id="DOC-000101"))
        with self.assertRaises(DisposicionYaRegistradaError) as contexto:
            self.repository.guardar(
                self._crear(
                    ordinal=2,
                    documento_op_id="DOC-000102",
                    numero_disposicion="1/2026",
                )
            )
        self.assertEqual(contexto.exception.criterio, "numero_disposicion")

    def test_listar_por_expediente_devuelve_todas_en_orden(self) -> None:
        segunda = self._crear(ordinal=2, documento_op_id="DOC-000102")
        primera = self._crear(ordinal=1, documento_op_id="DOC-000101")
        self.repository.guardar(segunda)
        self.repository.guardar(primera)
        self.assertEqual(
            self.repository.listar_por_expediente("EXP-1"),
            [primera, segunda],
        )
        with self.assertRaises(DisposicionExpedienteAmbiguoError):
            self.repository.obtener_por_expediente("EXP-1")

    def test_obtener_por_documento_op_devuelve_la_correcta(self) -> None:
        primera = self._crear(documento_op_id="DOC-000101")
        segunda = self._crear(ordinal=2, documento_op_id="DOC-000102")
        self.repository.guardar(primera)
        self.repository.guardar(segunda)
        self.assertEqual(
            self.repository.obtener_por_documento_op("DOC-000102"),
            segunda,
        )

    def test_historico_sin_documento_op_permanece_valido(self) -> None:
        historico = self._crear()
        self.repository.guardar(historico)
        self.assertEqual(self.repository.obtener_por_id(historico.id_disposicion), historico)

    def test_mapper_no_inventa_relaciones_historicas(self) -> None:
        modelo = a_modelo(self._crear())
        self.assertIsNone(modelo.documento_op_secuencia)
        self.assertIsNone(modelo.control_proveedor_op_id)
        self.assertIsNone(modelo.seleccion_proveedor_id)
        self.assertIsNone(modelo.proveedor_definitivo_id)
        self.assertIsNone(modelo.proveedor_definitivo_cuit)
        self.assertIsNone(modelo.proveedor_definitivo_razon_social)

    @classmethod
    def _crear(cls, ordinal: int = 1, **cambios) -> Disposicion:
        valores = {
            "id_disposicion": cls._uuid(ordinal),
            "expediente_id": "EXP-1",
            "configuracion_uc_id": "configuracion-1",
            "numero_disposicion": f"{ordinal}/2026",
            "fecha_emision": datetime(2026, 8, 11) + timedelta(seconds=ordinal),
            "fondo_interviniente": "FONDO_COMPENSADOR",
            "numero_op": f"OP-{ordinal}",
            "numero_liquidacion": None,
            "proveedor": "Proveedor",
            "cuit": "30-00000000-0",
            "importe": Decimal("1000.50"),
            "objeto": "Objeto",
            "establecimiento": "EP 1",
            "valor_uc_aplicado": Decimal("1677"),
            "cantidad_uc": Decimal("0.59660"),
            "procedimiento_contratacion": "Factura Conformada",
            "norma_uc": "Ley 13.981",
            "texto_emitido": "Texto emitido",
            "ruta_docx": f"exports/EXP-1/disposicion-{ordinal}.docx",
        }
        valores.update(cambios)
        return Disposicion(**valores)

    @staticmethod
    def _uuid(ordinal: int) -> str:
        return f"00000000-0000-0000-0000-{ordinal:012d}"
