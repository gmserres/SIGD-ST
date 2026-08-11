import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.expedientes import (
    _controlar_proveedor_op_o_error,
    consultar_control_proveedor_op,
    ejecutar_control_proveedor_op,
)
from app.schemas.control_proveedor_op import (
    EstadoControlProveedorOPAdministrativo,
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
        post = SimpleNamespace(
            estado=(
                EstadoControlProveedorOPAdministrativo.COINCIDE
            )
        )
        get = SimpleNamespace(
            estado=(
                EstadoControlProveedorOPAdministrativo.COINCIDE
            )
        )
        with patch(
            (
                "app.api.expedientes."
                "control_proveedor_op_service.ejecutar"
            ),
            return_value=post,
        ) as ejecutar:
            self.assertIs(
                ejecutar_control_proveedor_op("EXP-1", "DOC-1"),
                post,
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

        ejecutar.assert_called_once_with("EXP-1", "DOC-1")
        consultar.assert_called_once_with("EXP-1", "DOC-1")

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
