import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException, Response

from app.api.expedientes import (
    _controlar_proveedor_op_o_error,
    consultar_control_proveedor_op,
    ejecutar_control_proveedor_op,
)
from app.schemas.control_proveedor_op import (
    EstadoControlProveedorOPAdministrativo,
)
from app.repositories.control_proveedor_op_repository import (
    SeleccionControlObsoletaError,
)
from app.schemas.control_proveedor_op_registro import (
    ControlProveedorOPRegistroRead,
)
from app.services.analisis_op import (
    ArchivoOPNoAnalizableError,
    ArchivoOPNoDisponibleError,
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)


class ControlProveedorOPApiTest(unittest.TestCase):
    def test_api_devuelve_normalmente_los_cinco_estados(
        self,
    ) -> None:
        estados = tuple(EstadoControlProveedorOPAdministrativo)

        for estado in estados:
            esperado = SimpleNamespace(estado=estado)
            with self.subTest(estado=estado.value), patch(
                (
                    "app.api.expedientes."
                    "control_proveedor_op_service.ejecutar"
                ),
                return_value=esperado,
            ):
                resultado = _controlar_proveedor_op_o_error(
                    "EXP-1",
                    "DOC-1",
                )

            self.assertIs(resultado, esperado)

    def test_post_y_get_delegan_sin_persistir_control(
        self,
    ) -> None:
        get = SimpleNamespace(
            estado=(
                EstadoControlProveedorOPAdministrativo.COINCIDE
            )
        )
        with patch(
            (
                "app.api.expedientes."
                "control_proveedor_op_service.consultar"
            ),
            return_value=get,
        ) as consultar:
            self.assertIs(
                consultar_control_proveedor_op("EXP-1", "DOC-1"),
                get,
            )

        consultar.assert_called_once_with("EXP-1", "DOC-1")

    def test_post_persistido_responde_201(self) -> None:
        esperado = self._registro(
            id_control=(
                "00000000-0000-0000-0000-000000000501"
            ),
            fecha_control=datetime(2026, 8, 11, 15, 30),
        )
        response = Response()

        with patch(
            (
                "app.api.expedientes."
                "registrar_control_proveedor_op_service.ejecutar"
            ),
            return_value=esperado,
        ) as registrar:
            resultado = ejecutar_control_proveedor_op(
                "EXP-1", "DOC-1", response
            )

        self.assertIs(resultado, esperado)
        self.assertEqual(response.status_code, 201)
        registrar.assert_called_once_with("EXP-1", "DOC-1")

    def test_post_traduce_seleccion_obsoleta_a_409(self) -> None:
        response = Response()
        with patch(
            (
                "app.api.expedientes."
                "registrar_control_proveedor_op_service.ejecutar"
            ),
            side_effect=SeleccionControlObsoletaError(),
        ):
            with self.assertRaises(HTTPException) as contexto:
                ejecutar_control_proveedor_op("EXP-1", "DOC-1", response)
        self.assertEqual(contexto.exception.status_code, 409)

    def test_post_no_persistible_y_get_responden_200(
        self,
    ) -> None:
        post = self._registro(
            id_control=None,
            fecha_control=None,
            solicitud_intervencion_id=None,
            seleccion_proveedor_id=None,
            estado=(
                EstadoControlProveedorOPAdministrativo
                .SIN_SOLICITUD_ASOCIADA
            ),
            cuit_seleccionado=None,
            cuit_detectado=None,
            razon_social_seleccionada=None,
            razon_social_detectada=None,
            modo_analisis=None,
        )
        get = SimpleNamespace(
            estado=EstadoControlProveedorOPAdministrativo.COINCIDE
        )
        response = Response()

        with patch(
            (
                "app.api.expedientes."
                "registrar_control_proveedor_op_service.ejecutar"
            ),
            return_value=post,
        ):
            resultado_post = ejecutar_control_proveedor_op(
                "EXP-1", "DOC-1", response
            )
        with patch(
            (
                "app.api.expedientes."
                "control_proveedor_op_service.consultar"
            ),
            return_value=get,
        ):
            resultado_get = consultar_control_proveedor_op(
                "EXP-1", "DOC-1"
            )

        self.assertIs(resultado_post, post)
        self.assertEqual(response.status_code, 200)
        self.assertIs(resultado_get, get)

    def test_api_conserva_traducciones_http_f1(self) -> None:
        casos = (
            (KeyError("EXP-1"), 404),
            (DocumentoOPNoEncontradoError("DOC-1"), 404),
            (
                DocumentoOPExpedienteInconsistenteError(
                    "DOC-1",
                    "EXP-1",
                ),
                409,
            ),
            (DocumentoNoEsOPError("DOC-1"), 422),
            (ArchivoOPNoDisponibleError("DOC-1"), 409),
            (ArchivoOPNoAnalizableError("DOC-1"), 422),
        )

        for error, codigo in casos:
            with self.subTest(error=type(error).__name__), patch(
                (
                    "app.api.expedientes."
                    "control_proveedor_op_service.ejecutar"
                ),
                side_effect=error,
            ):
                with self.assertRaises(HTTPException) as contexto:
                    _controlar_proveedor_op_o_error(
                        "EXP-1",
                        "DOC-1",
                    )

            self.assertEqual(
                contexto.exception.status_code,
                codigo,
            )

    @staticmethod
    def _registro(**cambios) -> ControlProveedorOPRegistroRead:
        valores = {
            "id_control": None,
            "fecha_control": None,
            "expediente_id": "EXP-1",
            "documento_op_id": "DOC-1",
            "solicitud_intervencion_id": "SOL-1",
            "seleccion_proveedor_id": "SEL-1",
            "estado": EstadoControlProveedorOPAdministrativo.COINCIDE,
            "cuit_seleccionado": "30718078063",
            "cuit_detectado": "30718078063",
            "razon_social_seleccionada": "Proveedor A",
            "razon_social_detectada": "Proveedor A",
            "advertencias": [],
            "modo_analisis": "ALFA_PDF_TEXTO",
        }
        valores.update(cambios)
        return ControlProveedorOPRegistroRead(**valores)
