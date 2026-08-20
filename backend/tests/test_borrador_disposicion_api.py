import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.expedientes import (
    generar_borrador_disposicion,
    generar_borrador_disposicion_documento,
    obtener_borrador_disposicion_documento,
)
from app.domain.habilitacion_proveedor_op import (
    EstadoHabilitacionProveedorOP,
)
from app.services.disposiciones import (
    BorradorDisposicionLegacyDeshabilitadoError,
    BorradorDisposicionNoHabilitadoError,
)


class BorradorDisposicionApiTest(unittest.TestCase):
    def test_api_direccionada_delega_expediente_y_documento(self) -> None:
        esperado = SimpleNamespace(documento_op_id="DOC-1")
        with patch(
            "app.api.expedientes.obtener_expediente"
        ), patch(
            "app.api.expedientes.disposicion_service.generar_borrador",
            return_value=esperado,
        ) as generar, patch(
            "app.api.expedientes.disposicion_service.obtener_borrador",
            return_value=esperado,
        ) as obtener:
            self.assertIs(
                generar_borrador_disposicion_documento(
                    "EXP-1", "DOC-1", True
                ),
                esperado,
            )
            self.assertIs(
                obtener_borrador_disposicion_documento(
                    "EXP-1", "DOC-1"
                ),
                esperado,
            )
        generar.assert_called_once_with(
            "EXP-1", "DOC-1", regenerar=True
        )
        obtener.assert_called_once_with("EXP-1", "DOC-1")

    def test_api_traduce_f5_y_legacy_ambiguo_a_409(self) -> None:
        habilitacion = SimpleNamespace(
            estado=(
                EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL
            ),
            mensaje="Debe ejecutar un nuevo control.",
            proxima_accion="Ejecutar control.",
            documento_op_id="DOC-1",
        )
        error_f5 = BorradorDisposicionNoHabilitadoError(habilitacion)
        with patch(
            "app.api.expedientes.obtener_expediente"
        ), patch(
            "app.api.expedientes.disposicion_service.generar_borrador",
            side_effect=error_f5,
        ):
            with self.assertRaises(HTTPException) as contexto:
                generar_borrador_disposicion_documento(
                    "EXP-1", "DOC-1"
                )
        self.assertEqual(contexto.exception.status_code, 409)
        self.assertEqual(
            contexto.exception.detail["estado"],
            "REQUIERE_NUEVO_CONTROL",
        )
        self.assertEqual(
            contexto.exception.detail["documento_op_id"], "DOC-1"
        )

        with patch(
            "app.api.expedientes.obtener_expediente",
            return_value=SimpleNamespace(estado="VALIDADO"),
        ), patch(
            "app.api.expedientes.disposicion_service.generar_borrador_legacy",
            side_effect=BorradorDisposicionLegacyDeshabilitadoError(),
        ):
            with self.assertRaises(HTTPException) as contexto:
                generar_borrador_disposicion("EXP-1")
        self.assertEqual(contexto.exception.status_code, 409)
