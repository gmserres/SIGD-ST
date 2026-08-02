import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.api.expedientes import registrar_archivo
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.repositories.registrar_archivo_persistence import (
    ArchivoYaRegistradoError,
    EstadoExpedienteIncompatibleParaArchivoError,
    ExpedienteNoEncontradoAlRegistrarArchivoError,
    FechaArchivoAnteriorAFirmaError,
    FirmaAusenteOInconsistenteAlArchivarError,
)
from app.schemas.archivo import RegistroArchivoCreate
from app.services.registro_archivo import (
    FechaArchivoFuturaError,
    RegistroArchivoService,
    USUARIO_REGISTRO_ARCHIVO,
)


class RegistroArchivoServiceTest(unittest.TestCase):
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
            estado=EstadoExpediente.ARCHIVADO,
            establecimiento="EP 1",
            objeto="Compra",
            numero_disposicion="1/2026",
            creado=datetime(2026, 7, 30, 9),
            fecha_firma=date(2026, 8, 1),
            usuario_registro_firma="Secretario Técnico",
            fecha_archivo=date(2026, 8, 2),
            usuario_registro_archivo=USUARIO_REGISTRO_ARCHIVO,
        )
        self.service = RegistroArchivoService(
            self.persistence,
            today=lambda: date(2026, 8, 2),
        )

    def test_registra_usuario_backend_y_devuelve_expediente_archivado(self):
        resultado = self.service.registrar("EXP-1", date(2026, 8, 2))

        self.persistence.registrar.assert_called_once_with(
            "EXP-1",
            date(2026, 8, 2),
            "Secretario Técnico",
        )
        self.assertEqual(resultado.estado, EstadoExpediente.ARCHIVADO)
        self.assertEqual(resultado.fecha_archivo, date(2026, 8, 2))
        self.assertEqual(
            resultado.usuario_registro_archivo,
            "Secretario Técnico",
        )

    def test_rechaza_fecha_futura_sin_invocar_persistencia(self):
        with self.assertRaises(FechaArchivoFuturaError):
            self.service.registrar("EXP-1", date(2026, 8, 3))
        self.persistence.registrar.assert_not_called()


class RegistroArchivoApiTest(unittest.TestCase):
    def test_responde_expediente_actualizado(self):
        respuesta = MagicMock()
        service = MagicMock()
        service.registrar.return_value = respuesta
        with patch("app.api.expedientes.registro_archivo_service", service):
            resultado = registrar_archivo(
                "EXP-1",
                RegistroArchivoCreate(fecha_archivo=date(2026, 8, 2)),
            )
        self.assertIs(resultado, respuesta)
        service.registrar.assert_called_once_with(
            "EXP-1", date(2026, 8, 2)
        )

    def test_traduce_errores_funcionales(self):
        casos = (
            (ExpedienteNoEncontradoAlRegistrarArchivoError("EXP-1"), 404),
            (EstadoExpedienteIncompatibleParaArchivoError("EXP-1"), 409),
            (ArchivoYaRegistradoError("EXP-1"), 409),
            (FirmaAusenteOInconsistenteAlArchivarError("EXP-1"), 409),
            (FechaArchivoFuturaError("EXP-1"), 422),
            (FechaArchivoAnteriorAFirmaError("EXP-1"), 422),
        )
        for error, codigo in casos:
            with self.subTest(error=type(error).__name__):
                service = MagicMock()
                service.registrar.side_effect = error
                with (
                    patch(
                        "app.api.expedientes.registro_archivo_service",
                        service,
                    ),
                    self.assertRaises(HTTPException) as contexto,
                ):
                    registrar_archivo(
                        "EXP-1",
                        RegistroArchivoCreate(
                            fecha_archivo=date(2026, 8, 2)
                        ),
                    )
                self.assertEqual(contexto.exception.status_code, codigo)


if __name__ == "__main__":
    unittest.main()
