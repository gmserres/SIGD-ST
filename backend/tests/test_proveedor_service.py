import unittest

from app.domain.proveedor import (
    CuitProveedorDuplicadoError,
    Proveedor,
    normalizar_cuit,
)
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorEstadoUpdate,
    ProveedorUpdate,
)
from app.services.proveedor_service import ProveedorService


class ProveedorRepositoryFake:
    def __init__(self) -> None:
        self.proveedores: dict[str, Proveedor] = {}

    def guardar(self, proveedor: Proveedor) -> None:
        self.proveedores[proveedor.id_proveedor] = proveedor

    def obtener_por_id(self, proveedor_id: str) -> Proveedor | None:
        return self.proveedores.get(proveedor_id)

    def obtener_por_cuit(self, cuit: str) -> Proveedor | None:
        normalizado = normalizar_cuit(cuit)
        return next(
            (
                proveedor
                for proveedor in self.proveedores.values()
                if proveedor.cuit == normalizado
            ),
            None,
        )

    def listar(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = None,
    ) -> list[Proveedor]:
        proveedores = list(self.proveedores.values())
        if buscar:
            termino = buscar.strip()
            try:
                cuit = normalizar_cuit(termino)
            except (TypeError, ValueError):
                cuit = None
            proveedores = [
                proveedor
                for proveedor in proveedores
                if termino.casefold()
                in proveedor.razon_social.casefold()
                or (cuit is not None and cuit == proveedor.cuit)
            ]
        if activo is not None:
            proveedores = [
                proveedor
                for proveedor in proveedores
                if proveedor.activo == activo
            ]
        return sorted(
            proveedores,
            key=lambda proveedor: (
                proveedor.razon_social,
                proveedor.cuit,
                proveedor.id_proveedor,
            ),
        )


class ProveedorServiceTest(unittest.TestCase):
    def setUp(self):
        self.repository = ProveedorRepositoryFake()
        self.service = ProveedorService(self.repository)

    def test_registra_normaliza_cuit_y_genera_uuid(self):
        resultado = self._registrar()

        self.assertEqual(resultado.cuit, "30718078063")
        self.assertTrue(resultado.activo)
        self.assertTrue(resultado.id_proveedor)

    def test_rechaza_cuit_duplicado(self):
        self._registrar()

        with self.assertRaises(CuitProveedorDuplicadoError):
            self._registrar()

    def test_obtiene_por_id(self):
        registrado = self._registrar()

        self.assertEqual(
            self.service.obtener_por_id(registrado.id_proveedor),
            registrado,
        )

    def test_obtiene_por_cuit_con_guiones(self):
        registrado = self._registrar()

        self.assertEqual(
            self.service.obtener_por_cuit("30-71807806-3"),
            registrado,
        )

    def test_informa_proveedor_inexistente(self):
        with self.assertRaises(KeyError):
            self.service.obtener_por_id("inexistente")

    def test_lista_proveedores(self):
        registrado = self._registrar()

        self.assertEqual(self.service.listar(), [registrado])

    def test_busca_por_razon_social(self):
        registrado = self._registrar()

        self.assertEqual(
            self.service.listar(buscar="constructora"),
            [registrado],
        )

    def test_busca_por_cuit(self):
        registrado = self._registrar()

        self.assertEqual(
            self.service.listar(buscar="30-71807806-3"),
            [registrado],
        )

    def test_modifica_razon_social_preservando_identidad(self):
        original = self._registrar()

        actualizado = self.service.modificar_razon_social(
            original.id_proveedor,
            ProveedorUpdate(razon_social="Nueva Razón Social"),
        )

        self.assertEqual(actualizado.razon_social, "Nueva Razón Social")
        self.assertEqual(actualizado.cuit, original.cuit)
        self.assertEqual(actualizado.id_proveedor, original.id_proveedor)
        self.assertEqual(actualizado.activo, original.activo)

    def test_modificar_inexistente(self):
        with self.assertRaises(KeyError):
            self.service.modificar_razon_social(
                "inexistente",
                ProveedorUpdate(razon_social="Nueva Razón Social"),
            )

    def test_inactiva_y_reactiva_proveedor(self):
        original = self._registrar()

        inactivo = self.service.actualizar_estado(
            original.id_proveedor,
            ProveedorEstadoUpdate(activo=False),
        )
        reactivado = self.service.actualizar_estado(
            original.id_proveedor,
            ProveedorEstadoUpdate(activo=True),
        )

        self.assertFalse(inactivo.activo)
        self.assertTrue(reactivado.activo)

    def test_actualizar_estado_inexistente(self):
        with self.assertRaises(KeyError):
            self.service.actualizar_estado(
                "inexistente",
                ProveedorEstadoUpdate(activo=False),
            )

    def test_filtra_por_estado(self):
        registrado = self._registrar()

        self.assertEqual(
            self.service.listar(activo=True),
            [registrado],
        )
        self.assertEqual(self.service.listar(activo=False), [])

    def _registrar(self):
        return self.service.registrar(
            ProveedorCreate(
                cuit="30-71807806-3",
                razon_social="Constructora del Sur S.R.L.",
            )
        )
