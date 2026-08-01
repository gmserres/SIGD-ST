import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.expedientes import registrar_firma
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.repositories.registrar_firma_persistence import (
    DisposicionEmitidaNoEncontradaAlFirmarError,
    EstadoExpedienteIncompatibleParaFirmaError,
    ExpedienteNoEncontradoAlRegistrarFirmaError,
    FechaFirmaAnteriorAEmisionError,
    FirmaYaRegistradaError,
)
from app.schemas.firma import RegistroFirmaCreate
from app.services.registro_firma import (
    FechaFirmaFuturaError,
    RegistroFirmaService,
    USUARIO_REGISTRO_FIRMA,
)


class RegistroFirmaServiceTest(unittest.TestCase):
    def setUp(self):
        self.persistence = MagicMock()
        self.persistence.registrar.return_value = Expediente(
            id="EXP-1",
            numero_interno="033-1/2026",
            numero_gdeba=None,
            solicitud_intervencion_id="SOL-1",
            decision_administrativa_id="DEC-1",
            configuracion_uc_id="CONFIG-1",
            id_suna=None,
            tipo_tramite="FONDO_COMPENSADOR",
            estado=EstadoExpediente.FIRMADO,
            establecimiento="EP 1",
            objeto="Compra",
            numero_disposicion="1/2026",
            creado=datetime(2026, 7, 30, 9),
            fecha_firma=date(2026, 8, 1),
            usuario_registro_firma=USUARIO_REGISTRO_FIRMA,
        )
        self.service = RegistroFirmaService(
            self.persistence,
            today=lambda: date(2026, 8, 1),
        )

    def test_registra_usuario_backend_y_devuelve_expediente_actualizado(self):
        resultado = self.service.registrar("EXP-1", date(2026, 8, 1))

        self.persistence.registrar.assert_called_once_with(
            "EXP-1",
            date(2026, 8, 1),
            "Secretario Técnico",
        )
        self.assertEqual(resultado.estado, EstadoExpediente.FIRMADO)
        self.assertEqual(resultado.fecha_firma, date(2026, 8, 1))
        self.assertEqual(
            resultado.usuario_registro_firma,
            "Secretario Técnico",
        )

    def test_rechaza_fecha_futura_sin_invocar_persistencia(self):
        with self.assertRaises(FechaFirmaFuturaError):
            self.service.registrar("EXP-1", date(2026, 8, 2))
        self.persistence.registrar.assert_not_called()


class RegistroFirmaApiTest(unittest.TestCase):
    def test_responde_expediente_actualizado(self):
        respuesta = MagicMock()
        service = MagicMock()
        service.registrar.return_value = respuesta
        with patch("app.api.expedientes.registro_firma_service", service):
            resultado = registrar_firma(
                "EXP-1",
                RegistroFirmaCreate(fecha_firma=date(2026, 8, 1)),
            )
        self.assertIs(resultado, respuesta)
        service.registrar.assert_called_once_with(
            "EXP-1", date(2026, 8, 1)
        )

    def test_traduce_errores_funcionales(self):
        casos = (
            (ExpedienteNoEncontradoAlRegistrarFirmaError("EXP-1"), 404),
            (EstadoExpedienteIncompatibleParaFirmaError("EXP-1"), 409),
            (FirmaYaRegistradaError("EXP-1"), 409),
            (
                DisposicionEmitidaNoEncontradaAlFirmarError("EXP-1"),
                409,
            ),
            (FechaFirmaFuturaError("EXP-1"), 422),
            (FechaFirmaAnteriorAEmisionError("EXP-1"), 422),
        )
        for error, codigo in casos:
            with self.subTest(error=type(error).__name__):
                service = MagicMock()
                service.registrar.side_effect = error
                with (
                    patch(
                        "app.api.expedientes.registro_firma_service",
                        service,
                    ),
                    self.assertRaises(HTTPException) as contexto,
                ):
                    registrar_firma(
                        "EXP-1",
                        RegistroFirmaCreate(
                            fecha_firma=date(2026, 8, 1)
                        ),
                    )
                self.assertEqual(contexto.exception.status_code, codigo)


if __name__ == "__main__":
    unittest.main()
