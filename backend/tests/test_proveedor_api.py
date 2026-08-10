import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.api.proveedores import (
    actualizar_estado_proveedor,
    listar_proveedores,
    modificar_proveedor,
    obtener_proveedor,
    registrar_proveedor,
)
from app.domain.proveedor import CuitProveedorDuplicadoError
from app.schemas.proveedor import (
    ProveedorCreate,
    ProveedorEstadoUpdate,
    ProveedorRead,
    ProveedorUpdate,
)


class ProveedorApiTest(unittest.TestCase):
    def setUp(self):
        self.service = Mock()
        self.patch = patch(
            "app.api.proveedores.proveedor_service",
            self.service,
        )
        self.patch.start()
        self.proveedor = ProveedorRead(
            id_proveedor="00000000-0000-0000-0000-000000000001",
            cuit="30718078063",
            razon_social="Constructora del Sur S.R.L.",
            activo=True,
        )

    def tearDown(self):
        self.patch.stop()

    def test_post_registra_proveedor(self):
        self.service.registrar.return_value = self.proveedor

        respuesta = registrar_proveedor(
            ProveedorCreate(
                cuit="30-71807806-3",
                razon_social="Constructora del Sur S.R.L.",
            )
        )

        self.assertEqual(respuesta.cuit, "30718078063")

    def test_post_duplicado_devuelve_409(self):
        self.service.registrar.side_effect = (
            CuitProveedorDuplicadoError("CUIT duplicado.")
        )

        with self.assertRaises(HTTPException) as contexto:
            registrar_proveedor(
                ProveedorCreate(
                    cuit="30-71807806-3",
                    razon_social="Proveedor",
                )
            )

        self.assertEqual(contexto.exception.status_code, 409)

    def test_post_invalido_devuelve_422(self):
        self.service.registrar.side_effect = ValueError(
            "El CUIT es invalido."
        )

        with self.assertRaises(HTTPException) as contexto:
            registrar_proveedor(
                ProveedorCreate(
                    cuit="invalido",
                    razon_social="Proveedor",
                )
            )

        self.assertEqual(contexto.exception.status_code, 422)

    def test_get_lista(self):
        self.service.listar.return_value = [self.proveedor]

        respuesta = listar_proveedores()

        self.assertEqual(respuesta, [self.proveedor])

    def test_get_busqueda_y_estado(self):
        self.service.listar.return_value = [self.proveedor]

        listar_proveedores(buscar="constructora", activo=True)

        self.service.listar.assert_called_once_with(
            buscar="constructora",
            activo=True,
        )

    def test_get_por_id(self):
        self.service.obtener_por_id.return_value = self.proveedor

        respuesta = obtener_proveedor(self.proveedor.id_proveedor)

        self.assertEqual(respuesta, self.proveedor)

    def test_get_inexistente_devuelve_404(self):
        self.service.obtener_por_id.side_effect = KeyError("inexistente")

        with self.assertRaises(HTTPException) as contexto:
            obtener_proveedor("inexistente")

        self.assertEqual(contexto.exception.status_code, 404)

    def test_patch_modifica_razon_social(self):
        actualizado = self.proveedor.model_copy(
            update={"razon_social": "Nueva Razon Social"}
        )
        self.service.modificar_razon_social.return_value = actualizado

        respuesta = modificar_proveedor(
            self.proveedor.id_proveedor,
            ProveedorUpdate(razon_social="Nueva Razon Social"),
        )

        self.assertEqual(respuesta.razon_social, "Nueva Razon Social")

    def test_patch_razon_social_inexistente_devuelve_404(self):
        self.service.modificar_razon_social.side_effect = KeyError(
            "inexistente"
        )

        with self.assertRaises(HTTPException) as contexto:
            modificar_proveedor(
                "inexistente",
                ProveedorUpdate(razon_social="Nueva Razon Social"),
            )

        self.assertEqual(contexto.exception.status_code, 404)

    def test_patch_actualiza_estado(self):
        actualizado = self.proveedor.model_copy(update={"activo": False})
        self.service.actualizar_estado.return_value = actualizado

        respuesta = actualizar_estado_proveedor(
            self.proveedor.id_proveedor,
            ProveedorEstadoUpdate(activo=False),
        )

        self.assertFalse(respuesta.activo)

    def test_patch_estado_inexistente_devuelve_404(self):
        self.service.actualizar_estado.side_effect = KeyError("inexistente")

        with self.assertRaises(HTTPException) as contexto:
            actualizar_estado_proveedor(
                "inexistente",
                ProveedorEstadoUpdate(activo=False),
            )

        self.assertEqual(contexto.exception.status_code, 404)
