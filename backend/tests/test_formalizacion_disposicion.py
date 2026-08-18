import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.api.disposiciones import formalizar_disposicion
from app.domain.disposicion import Disposicion
from app.repositories.formalizacion_disposicion_persistence import (
    DisposicionNoEncontradaAlFormalizarError,
    DisposicionYaFormalizadaError,
    FechaFormalizacionAnteriorAEmisionError,
)
from app.schemas.formalizacion_disposicion import FormalizacionDisposicionCreate
from app.services.formalizacion_disposicion import (
    FechaFormalizacionFuturaError,
    FormalizacionDisposicionService,
    USUARIO_REGISTRO_FORMALIZACION,
)


AHORA = datetime(2026, 8, 18, 14, 30)


def disposicion() -> Disposicion:
    return Disposicion(
        id_disposicion="00000000-0000-0000-0000-000000000001",
        expediente_id="EXP-1",
        configuracion_uc_id="UC-1",
        numero_disposicion="100/2026",
        fecha_emision=datetime(2026, 8, 17, 10),
        fondo_interviniente="FONDO_COMPENSADOR",
        numero_op="OP-1",
        numero_liquidacion=None,
        proveedor="Proveedor",
        cuit="30999999991",
        importe=Decimal("100"),
        objeto="Objeto",
        establecimiento="EP 1",
        valor_uc_aplicado=Decimal("1"),
        cantidad_uc=Decimal("100"),
        procedimiento_contratacion="Procedimiento",
        norma_uc="Norma",
        texto_emitido="Texto inmutable",
        ruta_docx="exports/EXP-1/DOC-1/definitivas/disp.docx",
        documento_op_id="DOC-000001",
    )


class FormalizacionDisposicionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.persistence = Mock()
        self.service = FormalizacionDisposicionService(
            self.persistence, now=lambda: AHORA
        )

    def test_pendiente_derivado(self):
        resultado = self._schema(disposicion())
        self.assertEqual(resultado.estado_formalizacion, "PENDIENTE")

    def test_formalizada_derivada_y_metadatos(self):
        formalizada = replace(
            disposicion(),
            fecha_formalizacion=date(2026, 8, 18),
            usuario_registro_formalizacion="sistema",
            registrado_formalizacion_en=AHORA,
        )
        resultado = self._schema(formalizada)
        self.assertEqual(resultado.estado_formalizacion, "FORMALIZADA")
        self.assertEqual(resultado.usuario_registro_formalizacion, "sistema")

    def test_metadatos_parciales_invalidos(self):
        with self.assertRaises(ValueError):
            replace(
                disposicion(),
                fecha_formalizacion=date(2026, 8, 18),
            )

    def test_formaliza_con_usuario_neutral_y_timestamp_backend(self):
        formalizada = replace(
            disposicion(),
            fecha_formalizacion=date(2026, 8, 18),
            usuario_registro_formalizacion="sistema",
            registrado_formalizacion_en=AHORA,
        )
        self.persistence.formalizar.return_value = formalizada
        resultado = self.service.formalizar(
            disposicion().id_disposicion, date(2026, 8, 18)
        )
        self.persistence.formalizar.assert_called_once_with(
            disposicion().id_disposicion,
            date(2026, 8, 18),
            USUARIO_REGISTRO_FORMALIZACION,
            AHORA,
        )
        self.assertEqual(resultado.estado_formalizacion, "FORMALIZADA")

    def test_fecha_futura_rechazada_sin_persistir(self):
        with self.assertRaises(FechaFormalizacionFuturaError):
            self.service.formalizar(
                disposicion().id_disposicion, date(2026, 8, 19)
            )
        self.persistence.formalizar.assert_not_called()

    def test_inmutabilidad_del_acto_emitido(self):
        original = disposicion()
        formalizada = replace(
            original,
            fecha_formalizacion=date(2026, 8, 18),
            usuario_registro_formalizacion="sistema",
            registrado_formalizacion_en=AHORA,
        )
        for campo in (
            "numero_disposicion", "documento_op_id", "proveedor", "cuit",
            "texto_emitido", "ruta_docx", "expediente_id",
        ):
            self.assertEqual(getattr(formalizada, campo), getattr(original, campo))

    def test_api_inexistente_404(self):
        service = Mock()
        service.formalizar.side_effect = DisposicionNoEncontradaAlFormalizarError()
        with patch("app.api.disposiciones.formalizacion_disposicion_service", service):
            with self.assertRaises(HTTPException) as contexto:
                formalizar_disposicion("ausente", self._payload())
        self.assertEqual(contexto.exception.status_code, 404)

    def test_api_duplicada_409(self):
        service = Mock()
        service.formalizar.side_effect = DisposicionYaFormalizadaError()
        with patch("app.api.disposiciones.formalizacion_disposicion_service", service):
            with self.assertRaises(HTTPException) as contexto:
                formalizar_disposicion("id", self._payload())
        self.assertEqual(contexto.exception.status_code, 409)

    def test_api_fechas_invalidas_422(self):
        for error in (
            FechaFormalizacionFuturaError(),
            FechaFormalizacionAnteriorAEmisionError(),
        ):
            service = Mock()
            service.formalizar.side_effect = error
            with patch("app.api.disposiciones.formalizacion_disposicion_service", service):
                with self.assertRaises(HTTPException) as contexto:
                    formalizar_disposicion("id", self._payload())
            self.assertEqual(contexto.exception.status_code, 422)

    @staticmethod
    def _payload():
        return FormalizacionDisposicionCreate(
            fecha_formalizacion=date(2026, 8, 18)
        )

    @staticmethod
    def _schema(valor):
        from dataclasses import asdict
        from app.schemas.disposicion import DisposicionEmitidaRead
        return DisposicionEmitidaRead(**asdict(valor))


if __name__ == "__main__":
    unittest.main()
