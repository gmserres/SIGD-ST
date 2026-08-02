import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.disposicion_mapper import a_modelo
from app.infrastructure.database.models.disposicion_model import DisposicionModel
from app.infrastructure.database.persistence.registrar_archivo_postgres import (
    PostgresRegistrarArchivoPersistence,
)
from app.infrastructure.database.repositories.expediente_postgres_repository import (
    PostgresExpedienteRepository,
)
from app.repositories.registrar_archivo_persistence import (
    ArchivoYaRegistradoError,
    EstadoExpedienteIncompatibleParaArchivoError,
    ExpedienteNoEncontradoAlRegistrarArchivoError,
    FechaArchivoAnteriorAFirmaError,
    FirmaAusenteOInconsistenteAlArchivarError,
)


class RegistroArchivoPersistenciaTest(unittest.TestCase):
    """SQLite no valida el bloqueo real de SELECT FOR UPDATE."""

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self.persistence = PostgresRegistrarArchivoPersistence(self.factory)

    def tearDown(self):
        self.engine.dispose()

    def test_registra_persiste_y_preserva_firma_y_disposicion(self):
        self._guardar_expediente()
        original = self._guardar_disposicion()

        resultado = self.persistence.registrar(
            "EXP-1", date(2026, 8, 2), "Secretario Técnico"
        )

        self.assertEqual(resultado.estado, EstadoExpediente.ARCHIVADO)
        self.assertEqual(resultado.fecha_archivo, date(2026, 8, 2))
        self.assertEqual(
            resultado.usuario_registro_archivo, "Secretario Técnico"
        )
        self.assertEqual(resultado.fecha_firma, date(2026, 8, 1))
        self.assertEqual(
            resultado.usuario_registro_firma, "Secretario Técnico"
        )
        reconstruido = PostgresExpedienteRepository(
            self.factory
        ).obtener_por_id("EXP-1")
        self.assertEqual(reconstruido, resultado)
        with self.factory() as session:
            disposicion = session.get(
                DisposicionModel, original.id_disposicion
            )
            self.assertEqual(disposicion.fecha_emision, original.fecha_emision)
            self.assertEqual(disposicion.texto_emitido, original.texto_emitido)
            self.assertEqual(disposicion.ruta_docx, original.ruta_docx)

    def test_admite_misma_fecha_de_firma(self):
        self._guardar_expediente()
        resultado = self.persistence.registrar(
            "EXP-1", date(2026, 8, 1), "Secretario Técnico"
        )
        self.assertEqual(resultado.fecha_archivo, date(2026, 8, 1))

    def test_rechaza_expediente_inexistente(self):
        with self.assertRaises(ExpedienteNoEncontradoAlRegistrarArchivoError):
            self.persistence.registrar(
                "NO-EXISTE", date(2026, 8, 2), "Secretario Técnico"
            )

    def test_rechaza_estado_incompatible(self):
        self._guardar_expediente(estado=EstadoExpediente.VALIDADO)
        with self.assertRaises(EstadoExpedienteIncompatibleParaArchivoError):
            self.persistence.registrar(
                "EXP-1", date(2026, 8, 2), "Secretario Técnico"
            )

    def test_rechaza_archivo_duplicado(self):
        self._guardar_expediente()
        self.persistence.registrar(
            "EXP-1", date(2026, 8, 2), "Secretario Técnico"
        )
        with self.assertRaises(ArchivoYaRegistradoError):
            self.persistence.registrar(
                "EXP-1", date(2026, 8, 2), "Secretario Técnico"
            )

    def test_rechaza_metadatos_parciales_de_archivo(self):
        self._guardar_expediente(fecha_archivo=date(2026, 8, 2))
        with self.assertRaises(ArchivoYaRegistradoError):
            self.persistence.registrar(
                "EXP-1", date(2026, 8, 2), "Secretario Técnico"
            )

    def test_rechaza_firma_ausente_o_parcial(self):
        for fecha_firma, usuario_firma in (
            (None, None),
            (date(2026, 8, 1), None),
            (None, "Secretario Técnico"),
        ):
            with self.subTest(
                fecha_firma=fecha_firma,
                usuario_firma=usuario_firma,
            ):
                self._guardar_expediente(
                    expediente_id=f"EXP-{fecha_firma}-{usuario_firma}",
                    fecha_firma=fecha_firma,
                    usuario_firma=usuario_firma,
                )
                expediente_id = f"EXP-{fecha_firma}-{usuario_firma}"
                with self.assertRaises(
                    FirmaAusenteOInconsistenteAlArchivarError
                ):
                    self.persistence.registrar(
                        expediente_id,
                        date(2026, 8, 2),
                        "Secretario Técnico",
                    )

    def test_rechaza_fecha_anterior_a_firma(self):
        self._guardar_expediente()
        with self.assertRaises(FechaArchivoAnteriorAFirmaError):
            self.persistence.registrar(
                "EXP-1", date(2026, 7, 31), "Secretario Técnico"
            )

    def test_admite_archivado_historico_sin_metadatos(self):
        self._guardar_expediente(estado=EstadoExpediente.ARCHIVADO)
        reconstruido = PostgresExpedienteRepository(
            self.factory
        ).obtener_por_id("EXP-1")
        self.assertEqual(reconstruido.estado, EstadoExpediente.ARCHIVADO)
        self.assertIsNone(reconstruido.fecha_archivo)
        self.assertIsNone(reconstruido.usuario_registro_archivo)

    def test_ejecuta_un_flush_y_un_commit(self):
        session = MagicMock()
        session.scalar.return_value = self._modelo_expediente_mock()
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        PostgresRegistrarArchivoPersistence(factory).registrar(
            "EXP-1", date(2026, 8, 2), "Secretario Técnico"
        )
        session.flush.assert_called_once_with()
        session.commit.assert_called_once_with()
        session.rollback.assert_not_called()

    def test_rollback_completo_ante_error(self):
        session = MagicMock()
        session.scalar.return_value = self._modelo_expediente_mock()
        session.flush.side_effect = RuntimeError("fallo")
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session
        with self.assertRaisesRegex(RuntimeError, "fallo"):
            PostgresRegistrarArchivoPersistence(factory).registrar(
                "EXP-1", date(2026, 8, 2), "Secretario Técnico"
            )
        session.rollback.assert_called_once_with()
        session.commit.assert_not_called()

    def _guardar_expediente(
        self,
        estado=EstadoExpediente.FIRMADO,
        expediente_id="EXP-1",
        fecha_firma=date(2026, 8, 1),
        usuario_firma="Secretario Técnico",
        fecha_archivo=None,
    ):
        PostgresExpedienteRepository(self.factory).guardar(
            Expediente(
                id=expediente_id,
                numero_interno="033-1/2026",
                numero_gdeba=None,
                solicitud_intervencion_id="SOL-1",
                decision_administrativa_id="DEC-1",
                configuracion_uc_id=None,
                id_suna=None,
                tipo_tramite="FONDO_COMPENSADOR",
                estado=estado,
                establecimiento="EP 1",
                objeto="Compra",
                numero_disposicion="1/2026",
                creado=datetime(2026, 7, 30, 9),
                fecha_firma=fecha_firma,
                usuario_registro_firma=usuario_firma,
                fecha_archivo=fecha_archivo,
            )
        )

    def _guardar_disposicion(self):
        disposicion = Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000014",
            expediente_id="EXP-1",
            configuracion_uc_id="configuracion-1",
            numero_disposicion="1/2026",
            fecha_emision=datetime(2026, 7, 31, 10),
            fondo_interviniente="FONDO_COMPENSADOR",
            numero_op="OP-1",
            numero_liquidacion=None,
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe=Decimal("1000"),
            objeto="Compra",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.59630"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="Texto emitido",
            ruta_docx="exports/EXP-1/disposicion.docx",
        )
        with self.factory() as session:
            session.add(a_modelo(disposicion))
            session.commit()
        return disposicion

    @staticmethod
    def _modelo_expediente_mock():
        modelo = MagicMock()
        modelo.id = "EXP-1"
        modelo.numero_interno = "033-1/2026"
        modelo.numero_gdeba = None
        modelo.solicitud_intervencion_id = "SOL-1"
        modelo.decision_administrativa_id = "DEC-1"
        modelo.configuracion_uc_id = None
        modelo.id_suna = None
        modelo.tipo_tramite = "FONDO_COMPENSADOR"
        modelo.estado = EstadoExpediente.FIRMADO.value
        modelo.establecimiento = "EP 1"
        modelo.objeto = "Compra"
        modelo.numero_disposicion = "1/2026"
        modelo.creado = datetime(2026, 7, 30, 9)
        modelo.fecha_firma = date(2026, 8, 1)
        modelo.usuario_registro_firma = "Secretario Técnico"
        modelo.fecha_archivo = None
        modelo.usuario_registro_archivo = None
        return modelo


if __name__ == "__main__":
    unittest.main()
