import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.expedientes import consultar_habilitacion_proveedor_op
from app.services.analisis_op import (
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)


class HabilitacionProveedorOPApiTest(unittest.TestCase):
    def test_get_delega_y_no_persiste(self) -> None:
        esperado = SimpleNamespace(estado="HABILITADO")
        with patch(
            "app.api.expedientes.evaluar_habilitacion_proveedor_op_service.evaluar",
            return_value=esperado,
        ) as evaluar, patch(
            "app.api.expedientes.registrar_control_proveedor_op_service.ejecutar"
        ) as registrar:
            resultado = consultar_habilitacion_proveedor_op("EXP-1", "DOC-1")
        self.assertIs(resultado, esperado)
        evaluar.assert_called_once_with("EXP-1", "DOC-1")
        registrar.assert_not_called()

    def test_traducciones_http(self) -> None:
        casos = (
            (KeyError("EXP-1"), 404),
            (DocumentoOPNoEncontradoError("DOC-1"), 404),
            (DocumentoOPExpedienteInconsistenteError("DOC-1", "EXP-1"), 409),
            (DocumentoNoEsOPError("DOC-1"), 422),
        )
        for error, codigo in casos:
            with self.subTest(error=type(error).__name__), patch(
                "app.api.expedientes.evaluar_habilitacion_proveedor_op_service.evaluar",
                side_effect=error,
            ):
                with self.assertRaises(HTTPException) as contexto:
                    consultar_habilitacion_proveedor_op("EXP-1", "DOC-1")
            self.assertEqual(contexto.exception.status_code, codigo)
