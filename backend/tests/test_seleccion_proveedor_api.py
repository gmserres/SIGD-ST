import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.api.selecciones_proveedor import (
    listar_selecciones_proveedor,
    obtener_seleccion_vigente,
    reemplazar_proveedor,
    router,
    seleccionar_proveedor,
)
from app.domain.seleccion_proveedor import (
    DecisionNoAprobatoriaError,
    MismoProveedorSeleccionadoError,
    ProveedorInactivoError,
    SeleccionProveedorInexistenteError,
    SeleccionProveedorVigenteError,
    SolicitudSeleccionInexistenteError,
)
from app.schemas.seleccion_proveedor import ReemplazoProveedorCreate, SeleccionProveedorCreate, SeleccionProveedorRead


SOLICITUD_ID = "00000000-0000-0000-0000-000000000201"
DECISION_ID = "00000000-0000-0000-0000-000000000301"
PROVEEDOR_ID = "00000000-0000-0000-0000-000000000401"
PROVEEDOR_NUEVO_ID = "00000000-0000-0000-0000-000000000402"
SELECCION_ID = "00000000-0000-0000-0000-000000000101"


class SeleccionProveedorApiTest(unittest.TestCase):
    def setUp(self):
        self.service = Mock()
        self.patch = patch(
            "app.api.selecciones_proveedor.seleccion_proveedor_service",
            self.service,
        )
        self.patch.start()
        self.seleccion = SeleccionProveedorRead(
            id_seleccion=SELECCION_ID,
            solicitud_intervencion_id=SOLICITUD_ID,
            decision_administrativa_id=DECISION_ID,
            proveedor_id=PROVEEDOR_ID,
            fecha_seleccion=datetime(2026, 8, 10, 10, 30),
            seleccionado_por="Secretaría Técnica",
            proveedor_cuit="30718078063",
            proveedor_razon_social="Proveedor Original",
            motivo_reemplazo=None,
            vigente=True,
        )

    def tearDown(self):
        self.patch.stop()

    def test_endpoints_post_declaran_http_201(self):
        seleccion = next(
            ruta
            for ruta in router.routes
            if isinstance(ruta, APIRoute)
            and ruta.path == "/{solicitud_id}/seleccion-proveedor"
            and "POST" in ruta.methods
        )
        reemplazo = next(
            ruta
            for ruta in router.routes
            if isinstance(ruta, APIRoute)
            and ruta.path
            == "/{solicitud_id}/seleccion-proveedor/reemplazos"
            and "POST" in ruta.methods
        )
        self.assertIn("POST", seleccion.methods)
        self.assertEqual(seleccion.status_code, 201)
        self.assertIn("POST", reemplazo.methods)
        self.assertEqual(reemplazo.status_code, 201)

    def test_post_selecciona_proveedor(self):
        self.service.seleccionar.return_value = self.seleccion
        data = SeleccionProveedorCreate(proveedor_id=PROVEEDOR_ID, seleccionado_por="Secretaría Técnica")
        self.assertEqual(seleccionar_proveedor(SOLICITUD_ID, data), self.seleccion)
        self.service.seleccionar.assert_called_once_with(SOLICITUD_ID, data)

    def test_get_devuelve_vigente_e_historial(self):
        historica = self.seleccion.model_copy(update={"vigente": False})
        self.service.obtener_vigente.return_value = self.seleccion
        self.service.listar_historial.return_value = [historica, self.seleccion]
        self.assertEqual(obtener_seleccion_vigente(SOLICITUD_ID), self.seleccion)
        self.assertEqual(listar_selecciones_proveedor(SOLICITUD_ID), [historica, self.seleccion])

    def test_post_reemplaza_proveedor(self):
        reemplazo = self.seleccion.model_copy(update={
            "proveedor_id": PROVEEDOR_NUEVO_ID,
            "proveedor_cuit": "30000000007",
            "proveedor_razon_social": "Proveedor Nuevo",
            "motivo_reemplazo": "Imposibilidad de cumplimiento",
        })
        self.service.reemplazar.return_value = reemplazo
        data = ReemplazoProveedorCreate(
            proveedor_id=PROVEEDOR_NUEVO_ID,
            seleccionado_por="Secretaría Técnica",
            motivo_reemplazo="Imposibilidad de cumplimiento",
        )
        self.assertEqual(reemplazar_proveedor(SOLICITUD_ID, data), reemplazo)
        self.service.reemplazar.assert_called_once_with(SOLICITUD_ID, data)

    def test_traduce_recursos_inexistentes_a_http_404(self):
        for error in (
            SolicitudSeleccionInexistenteError("Solicitud no encontrada."),
            SeleccionProveedorInexistenteError("Selección no encontrada."),
        ):
            with self.subTest(error=type(error).__name__):
                self.service.obtener_vigente.side_effect = error
                with self.assertRaises(HTTPException) as contexto:
                    obtener_seleccion_vigente(SOLICITUD_ID)
                self.assertEqual(contexto.exception.status_code, 404)

    def test_traduce_conflictos_de_seleccion_a_http_409(self):
        for error in (
            DecisionNoAprobatoriaError("La última Decisión no aprueba."),
            ProveedorInactivoError("Proveedor inactivo."),
            SeleccionProveedorVigenteError("Ya existe selección vigente."),
        ):
            with self.subTest(error=type(error).__name__):
                self.service.seleccionar.side_effect = error
                with self.assertRaises(HTTPException) as contexto:
                    seleccionar_proveedor(SOLICITUD_ID, SeleccionProveedorCreate(
                        proveedor_id=PROVEEDOR_ID,
                        seleccionado_por="Secretaría Técnica",
                    ))
                self.assertEqual(contexto.exception.status_code, 409)

    def test_traduce_conflicto_de_reemplazo_a_http_409(self):
        self.service.reemplazar.side_effect = MismoProveedorSeleccionadoError(
            "El Proveedor ya está seleccionado."
        )
        with self.assertRaises(HTTPException) as contexto:
            reemplazar_proveedor(SOLICITUD_ID, ReemplazoProveedorCreate(
                proveedor_id=PROVEEDOR_ID,
                seleccionado_por="Secretaría Técnica",
                motivo_reemplazo="Reasignación",
            ))
        self.assertEqual(contexto.exception.status_code, 409)

    def test_traduce_datos_invalidos_a_http_422(self):
        self.service.reemplazar.side_effect = ValueError(
            "El motivo del reemplazo es obligatorio."
        )
        data = ReemplazoProveedorCreate.model_construct(
            proveedor_id=PROVEEDOR_NUEVO_ID,
            seleccionado_por="Secretaría Técnica",
            motivo_reemplazo="",
        )
        with self.assertRaises(HTTPException) as contexto:
            reemplazar_proveedor(SOLICITUD_ID, data)
        self.assertEqual(contexto.exception.status_code, 422)
