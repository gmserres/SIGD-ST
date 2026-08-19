import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.expedientes import archivar_expediente_finalizado
from app.domain.estados import EstadoExpediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.persistence.registrar_archivo_postgres import (
    PostgresRegistrarArchivoPersistence,
)
from app.repositories.registrar_archivo_persistence import (
    ArchivoYaRegistradoError,
    EstadoExpedienteIncompatibleParaArchivoError,
    ExpedienteNoEncontradoAlRegistrarArchivoError,
    FechaArchivoAnteriorAFinalizacionError,
)
from app.schemas.archivo import RegistroArchivoCreate
from app.services.registro_archivo import (
    FechaArchivoFuturaError,
    RegistroArchivoService,
)


class ArchivoExpedienteFinalizadoTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        self.persistence = PostgresRegistrarArchivoPersistence(self.factory)

    def tearDown(self):
        self.engine.dispose()

    def _guardar(self, estado="CERRADO", expediente_id="EXP-1"):
        cierre = estado == "CERRADO"
        desistido = estado == "DESISTIDO"
        with self.factory() as session:
            session.add(ExpedienteModel(
                id=expediente_id,
                numero_interno=f"{expediente_id}/2026",
                numero_gdeba=None,
                solicitud_intervencion_id=None,
                decision_administrativa_id=None,
                configuracion_uc_id=None,
                id_suna=None,
                tipo_tramite="FONDO_COMPENSADOR",
                estado=estado,
                establecimiento="EP 1",
                objeto="Obra",
                numero_disposicion=None,
                creado=datetime(2026, 8, 1, 10),
                fecha_cierre=date(2026, 8, 18) if cierre else None,
                usuario_registro_cierre="sistema" if cierre else None,
                registrado_cierre_en=datetime(2026, 8, 18, 12) if cierre else None,
                fecha_desistimiento=date(2026, 8, 17) if desistido else None,
                usuario_registro_desistimiento="sistema" if desistido else None,
                registrado_desistimiento_en=datetime(2026, 8, 17, 12) if desistido else None,
                motivo_desistimiento="Presupuesto no aceptado" if desistido else None,
            ))
            session.commit()

    def test_cerrado_pasa_a_archivado_y_preserva_causa(self):
        self._guardar()
        resultado = self.persistence.registrar_finalizado(
            "EXP-1", date(2026, 8, 19), "sistema"
        )
        self.assertEqual(EstadoExpediente.ARCHIVADO, resultado.estado)
        self.assertEqual(date(2026, 8, 19), resultado.fecha_archivo)
        self.assertEqual("sistema", resultado.usuario_registro_archivo)
        self.assertEqual(date(2026, 8, 18), resultado.fecha_cierre)
        self.assertIsNone(resultado.fecha_desistimiento)

    def test_desistido_pasa_a_archivado_y_preserva_motivo(self):
        self._guardar("DESISTIDO")
        resultado = self.persistence.registrar_finalizado(
            "EXP-1", date(2026, 8, 19), "sistema"
        )
        self.assertEqual(EstadoExpediente.ARCHIVADO, resultado.estado)
        self.assertEqual(date(2026, 8, 17), resultado.fecha_desistimiento)
        self.assertEqual("Presupuesto no aceptado", resultado.motivo_desistimiento)
        self.assertIsNone(resultado.fecha_cierre)

    def test_misma_fecha_de_finalizacion_es_admitida(self):
        for estado, fecha in (("CERRADO", date(2026, 8, 18)), ("DESISTIDO", date(2026, 8, 17))):
            with self.subTest(estado=estado):
                expediente_id = f"EXP-{estado}"
                self._guardar(estado, expediente_id)
                resultado = self.persistence.registrar_finalizado(
                    expediente_id, fecha, "sistema"
                )
                self.assertEqual(fecha, resultado.fecha_archivo)

    def test_fecha_anterior_a_finalizacion_es_rechazada(self):
        for estado, fecha in (("CERRADO", date(2026, 8, 17)), ("DESISTIDO", date(2026, 8, 16))):
            with self.subTest(estado=estado):
                expediente_id = f"EXP-{estado}"
                self._guardar(estado, expediente_id)
                with self.assertRaises(FechaArchivoAnteriorAFinalizacionError):
                    self.persistence.registrar_finalizado(
                        expediente_id, fecha, "sistema"
                    )

    def test_estado_operativo_es_rechazado(self):
        self._guardar("VALIDADO")
        with self.assertRaises(EstadoExpedienteIncompatibleParaArchivoError):
            self.persistence.registrar_finalizado(
                "EXP-1", date(2026, 8, 19), "sistema"
            )

    def test_segundo_archivo_no_sobrescribe(self):
        self._guardar()
        self.persistence.registrar_finalizado(
            "EXP-1", date(2026, 8, 18), "sistema"
        )
        with self.assertRaises(ArchivoYaRegistradoError):
            self.persistence.registrar_finalizado(
                "EXP-1", date(2026, 8, 19), "otro"
            )
        with self.factory() as session:
            modelo = session.scalar(select(ExpedienteModel).where(ExpedienteModel.id == "EXP-1"))
            self.assertEqual(date(2026, 8, 18), modelo.fecha_archivo)
            self.assertEqual("sistema", modelo.usuario_registro_archivo)

    def test_inexistente_es_rechazado(self):
        with self.assertRaises(ExpedienteNoEncontradoAlRegistrarArchivoError):
            self.persistence.registrar_finalizado(
                "NO-EXISTE", date(2026, 8, 19), "sistema"
            )


class ArchivoExpedienteFinalizadoServiceApiTest(unittest.TestCase):
    def test_service_usa_usuario_tecnico(self):
        persistence = MagicMock()
        persistence.registrar_finalizado.return_value = MagicMock()
        service = RegistroArchivoService(
            persistence, today=lambda: date(2026, 8, 19)
        )
        with patch("app.services.registro_archivo.asdict", return_value={
            "id": "EXP-1", "numero_interno": "1", "numero_gdeba": None,
            "solicitud_intervencion_id": None, "decision_administrativa_id": None,
            "configuracion_uc_id": None, "id_suna": None,
            "tipo_tramite": "FONDO_COMPENSADOR", "estado": "ARCHIVADO",
            "establecimiento": None, "objeto": None, "numero_disposicion": None,
            "creado": datetime(2026, 8, 1),
        }):
            service.registrar_finalizado("EXP-1", date(2026, 8, 19))
        persistence.registrar_finalizado.assert_called_once_with(
            "EXP-1", date(2026, 8, 19), "sistema"
        )

    def test_service_rechaza_fecha_futura(self):
        persistence = MagicMock()
        service = RegistroArchivoService(
            persistence, today=lambda: date(2026, 8, 19)
        )
        with self.assertRaises(FechaArchivoFuturaError):
            service.registrar_finalizado("EXP-1", date(2026, 8, 20))
        persistence.registrar_finalizado.assert_not_called()

    def test_api_responde_y_traduce_errores(self):
        service = MagicMock()
        service.registrar_finalizado.return_value = "actualizado"
        with patch("app.api.expedientes.registro_archivo_service", service):
            self.assertEqual("actualizado", archivar_expediente_finalizado(
                "EXP-1", RegistroArchivoCreate(fecha_archivo=date(2026, 8, 19))
            ))
        casos = (
            (ExpedienteNoEncontradoAlRegistrarArchivoError("EXP-1"), 404),
            (EstadoExpedienteIncompatibleParaArchivoError("EXP-1"), 409),
            (ArchivoYaRegistradoError("EXP-1"), 409),
            (FechaArchivoFuturaError("EXP-1"), 422),
            (FechaArchivoAnteriorAFinalizacionError("EXP-1", "CERRADO"), 422),
        )
        for error, status in casos:
            with self.subTest(error=type(error).__name__):
                service = MagicMock()
                service.registrar_finalizado.side_effect = error
                with patch("app.api.expedientes.registro_archivo_service", service), self.assertRaises(HTTPException) as ctx:
                    archivar_expediente_finalizado(
                        "EXP-1", RegistroArchivoCreate(fecha_archivo=date(2026, 8, 19))
                    )
                self.assertEqual(status, ctx.exception.status_code)


if __name__ == "__main__":
    unittest.main()
