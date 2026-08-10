import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.domain.proveedor import Proveedor
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.proveedor_mapper import (
    a_dominio,
    a_modelo,
)
from app.infrastructure.database.models.proveedor_model import (
    ProveedorModel,
)
from app.infrastructure.database.repositories.proveedor_postgres_repository import (
    PostgresProveedorRepository,
)


class ProveedorPersistenciaTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self.repository = PostgresProveedorRepository(self.factory)

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_mapper_ida_y_vuelta(self):
        original = self._crear()

        reconstruido = a_dominio(a_modelo(original))

        self.assertEqual(reconstruido, original)

    def test_guarda_y_recupera_por_id(self):
        original = self._crear()

        self.repository.guardar(original)
        recuperado = self.repository.obtener_por_id(
            original.id_proveedor
        )

        self.assertEqual(recuperado, original)

    def test_persiste_cuit_normalizado(self):
        proveedor = self._crear(cuit="30-71807806-3")

        self.repository.guardar(proveedor)

        with self.factory() as session:
            cuit_persistido = session.scalar(
                select(ProveedorModel.cuit).where(
                    ProveedorModel.id_proveedor
                    == proveedor.id_proveedor
                )
            )

        self.assertEqual(cuit_persistido, "30718078063")

    def test_obtiene_por_cuit_con_guiones(self):
        proveedor = self._crear(cuit="30718078063")
        self.repository.guardar(proveedor)

        recuperado = self.repository.obtener_por_cuit(
            "30-71807806-3"
        )

        self.assertEqual(recuperado, proveedor)

    def test_lista_en_orden_estable(self):
        primero = self._crear(
            id_proveedor=(
                "00000000-0000-0000-0000-000000000001"
            ),
            cuit="30718078063",
            razon_social="Proveedor B",
        )
        segundo = self._crear(
            id_proveedor=(
                "00000000-0000-0000-0000-000000000002"
            ),
            cuit="30000000007",
            razon_social="Proveedor A",
        )
        self.repository.guardar(primero)
        self.repository.guardar(segundo)

        proveedores = self.repository.listar()

        self.assertEqual(proveedores, [segundo, primero])

    def test_actualiza_razon_social_y_estado_preservando_cuit(self):
        original = self._crear()
        self.repository.guardar(original)

        actualizado = original.modificar_razon_social(
            "Razón Social Actualizada"
        ).inactivar()
        self.repository.guardar(actualizado)

        recuperado = self.repository.obtener_por_id(
            original.id_proveedor
        )
        self.assertEqual(
            recuperado.razon_social,
            "Razón Social Actualizada",
        )
        self.assertFalse(recuperado.activo)
        self.assertEqual(recuperado.cuit, original.cuit)

    def test_preserva_proveedor_inactivo(self):
        inactivo = self._crear().inactivar()

        self.repository.guardar(inactivo)

        self.assertEqual(
            self.repository.obtener_por_id(inactivo.id_proveedor),
            inactivo,
        )

    def test_rechaza_cuit_duplicado(self):
        primero = self._crear(
            id_proveedor=(
                "00000000-0000-0000-0000-000000000001"
            ),
        )
        segundo = self._crear(
            id_proveedor=(
                "00000000-0000-0000-0000-000000000002"
            ),
        )
        self.repository.guardar(primero)

        with self.assertRaises(IntegrityError):
            self.repository.guardar(segundo)

    def test_busca_por_razon_social_sin_distinguir_mayusculas(self):
        esperado = self._crear(razon_social="Servicios del Sur")
        self.repository.guardar(esperado)

        self.assertEqual(
            self.repository.listar(buscar="SERVICIOS"),
            [esperado],
        )

    def test_busca_por_cuit_normalizado(self):
        esperado = self._crear()
        self.repository.guardar(esperado)

        self.assertEqual(
            self.repository.listar(buscar="30-71807806-3"),
            [esperado],
        )

    def test_filtra_por_estado_activo(self):
        activo = self._crear()
        inactivo = self._crear(
            id_proveedor=(
                "00000000-0000-0000-0000-000000000002"
            ),
            cuit="30000000007",
        ).inactivar()
        self.repository.guardar(activo)
        self.repository.guardar(inactivo)

        self.assertEqual(
            self.repository.listar(activo=False),
            [inactivo],
        )

    @staticmethod
    def _crear(
        *,
        id_proveedor: str = (
            "00000000-0000-0000-0000-000000000001"
        ),
        cuit: str = "30-71807806-3",
        razon_social: str = "Constructora del Sur S.R.L.",
        activo: bool = True,
    ) -> Proveedor:
        return Proveedor(
            id_proveedor=id_proveedor,
            cuit=cuit,
            razon_social=razon_social,
            activo=activo,
        )
