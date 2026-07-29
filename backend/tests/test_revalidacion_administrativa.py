import importlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateIndex

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.checklist_fisico_model import (
    ChecklistFisicoModel,
)
from app.infrastructure.database.models.documento_model import (
    DocumentoModel,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.models.validacion_administrativa_model import (
    ValidacionAdministrativaModel,
    ValidacionControlModel,
)
from app.infrastructure.database.persistence.actualizar_checklist_postgres import (
    PostgresActualizarChecklistPersistence,
)
from app.infrastructure.database.persistence.cargar_op_postgres import (
    PostgresCargarOPPersistence,
)
from app.infrastructure.database.persistence.validar_expediente_postgres import (
    PostgresValidarExpedientePersistence,
)
from app.infrastructure.database.repositories.expediente_postgres_repository import (
    PostgresExpedienteRepository,
)
from app.infrastructure.database.repositories.validacion_administrativa_postgres_repository import (
    PostgresValidacionAdministrativaRepository,
)
from app.schemas.checklist_fisico import ChecklistFisicoRead
from app.schemas.documento import DocumentoCreate
from app.schemas.validacion import (
    ControlValidacionSnapshotRead,
    ValidacionAdministrativaRead,
)


class RevalidacionAdministrativaTest(unittest.TestCase):
    """SQLite no valida el bloqueo real de SELECT FOR UPDATE."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self._guardar_expediente()
        self.repository = PostgresValidacionAdministrativaRepository(
            self.factory
        )
        self.validar_persistence = (
            PostgresValidarExpedientePersistence(self.factory)
        )

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_revalidacion_invalida_anterior_y_deja_una_vigente(
        self,
    ) -> None:
        _, primera = self.validar_persistence.validar(
            self._validacion()
        )
        _, segunda = self.validar_persistence.validar(
            self._validacion(
                fecha=datetime(2026, 7, 29, 11),
                usuario="Revalidador",
                resultado="VALIDADA_CON_OBSERVACIONES",
                motivo_observacion="Revalidación con observaciones.",
            )
        )

        actos = self.repository.listar_por_expediente("EXP-1")
        vigente = self.repository.obtener_vigente("EXP-1")

        self.assertEqual(vigente.id, segunda.id)
        self.assertEqual(actos[0].id, primera.id)
        self.assertEqual(
            actos[0].fecha_invalidacion,
            datetime(2026, 7, 29, 11),
        )
        self.assertEqual(
            actos[0].motivo_invalidacion,
            "Reemplazada por nueva validación administrativa",
        )
        self.assertEqual(
            actos[0].usuario_invalidacion,
            "Revalidador",
        )
        self.assertEqual(actos[0].resultado, "VALIDADA")
        self.assertEqual(actos[0].controles[0].estado, "OK")
        self.assertIsNone(actos[1].fecha_invalidacion)
        with self.factory() as session:
            expediente = session.scalar(
                select(ExpedienteModel).where(
                    ExpedienteModel.id == "EXP-1"
                )
            )
        self.assertEqual(
            expediente.estado,
            EstadoExpediente.VALIDADO.value,
        )

    def test_indice_rechaza_dos_validaciones_vigentes(self) -> None:
        self.repository.registrar(self._validacion())

        with self.factory() as session:
            session.add(
                ValidacionAdministrativaModel(
                    expediente_id="EXP-1",
                    resultado="VALIDADA",
                    usuario="Otro",
                    fecha_validacion=datetime(2026, 7, 29, 11),
                    motivo_observacion=None,
                    estado_expediente="VALIDADO",
                    controles=[],
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_invalidacion_es_persistente_e_idempotente(self) -> None:
        _, original = self.validar_persistence.validar(
            self._validacion()
        )
        fecha = datetime(2026, 7, 29, 12)

        invalidada = self.repository.invalidar_vigente(
            "EXP-1",
            "Cambio material",
            "Operador",
            fecha,
        )
        segunda = self.repository.invalidar_vigente(
            "EXP-1",
            "Otro motivo",
            "Otro operador",
            datetime(2026, 7, 29, 13),
        )

        self.assertEqual(invalidada.id, original.id)
        self.assertEqual(invalidada.fecha_invalidacion, fecha)
        self.assertEqual(invalidada.motivo_invalidacion, "Cambio material")
        self.assertEqual(invalidada.usuario_invalidacion, "Operador")
        self.assertIsNone(segunda)
        recuperada = self.repository.listar_por_expediente("EXP-1")[0]
        self.assertEqual(recuperada.resultado, original.resultado)
        self.assertEqual(recuperada.usuario, original.usuario)
        self.assertEqual(
            recuperada.fecha_validacion,
            original.fecha_validacion,
        )
        self.assertEqual(recuperada.controles, original.controles)

    def test_checklist_invalida_y_deja_pendiente_revalidacion(
        self,
    ) -> None:
        self.validar_persistence.validar(self._validacion())

        guardado = PostgresActualizarChecklistPersistence(
            self.factory
        ).guardar(self._checklist())

        self.assertFalse(guardado.arba)
        self.assertIsNone(self.repository.obtener_vigente("EXP-1"))
        acto = self.repository.listar_por_expediente("EXP-1")[0]
        self.assertEqual(
            acto.motivo_invalidacion,
            "Modificación del checklist físico posterior a la "
            "validación",
        )
        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.PENDIENTE_REVALIDACION.value,
        )

    def test_checklist_sin_vigente_conserva_estado(self) -> None:
        PostgresActualizarChecklistPersistence(self.factory).guardar(
            self._checklist()
        )

        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.BORRADOR.value,
        )

    def test_fallo_de_estado_revierte_checklist_e_invalidacion(
        self,
    ) -> None:
        self.validar_persistence.validar(self._validacion())
        persistence = PostgresActualizarChecklistPersistence(
            self.factory
        )

        def fallar_estado(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            if "UPDATE expedientes" in statement:
                raise RuntimeError("fallo de estado")

        event.listen(
            self.engine,
            "before_cursor_execute",
            fallar_estado,
        )
        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "fallo de estado",
            ):
                persistence.guardar(self._checklist())
        finally:
            event.remove(
                self.engine,
                "before_cursor_execute",
                fallar_estado,
            )

        with self.factory() as session:
            cantidad = session.scalar(
                select(func.count()).select_from(
                    ChecklistFisicoModel
                )
            )
        self.assertEqual(cantidad, 0)
        self.assertIsNotNone(self.repository.obtener_vigente("EXP-1"))
        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.VALIDADO.value,
        )

    def test_fallo_de_invalidacion_revierte_checklist(self) -> None:
        self.validar_persistence.validar(self._validacion())
        persistence = PostgresActualizarChecklistPersistence(
            self.factory
        )

        def fallar_invalidacion(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            if "UPDATE validaciones_administrativas" in statement:
                raise RuntimeError("fallo de invalidación")

        event.listen(
            self.engine,
            "before_cursor_execute",
            fallar_invalidacion,
        )
        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "fallo de invalidación",
            ):
                persistence.guardar(self._checklist())
        finally:
            event.remove(
                self.engine,
                "before_cursor_execute",
                fallar_invalidacion,
            )

        with self.factory() as session:
            cantidad = session.scalar(
                select(func.count()).select_from(
                    ChecklistFisicoModel
                )
            )
        self.assertEqual(cantidad, 0)
        self.assertIsNotNone(self.repository.obtener_vigente("EXP-1"))
        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.VALIDADO.value,
        )

    def test_carga_op_invalida_y_deja_pendiente_revalidacion(
        self,
    ) -> None:
        self.validar_persistence.validar(self._validacion())

        documento = PostgresCargarOPPersistence(
            self.factory
        ).guardar(
            "EXP-1",
            self._op(),
            datetime(2026, 7, 29, 12),
        )

        self.assertEqual(documento.tipo, "OP")
        self.assertIsNone(self.repository.obtener_vigente("EXP-1"))
        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.PENDIENTE_REVALIDACION.value,
        )
        acto = self.repository.listar_por_expediente("EXP-1")[0]
        self.assertEqual(
            acto.motivo_invalidacion,
            "Carga de OP posterior a la validación administrativa",
        )

    def test_carga_op_sin_vigente_mantiene_regla_actual(self) -> None:
        PostgresCargarOPPersistence(self.factory).guardar(
            "EXP-1",
            self._op(),
            datetime(2026, 7, 29, 12),
        )

        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.DOCUMENTACION_EN_CARGA.value,
        )

    def test_fallo_de_op_no_deja_metadatos_parciales(self) -> None:
        self.validar_persistence.validar(self._validacion())
        persistence = PostgresCargarOPPersistence(self.factory)

        def fallar_estado(
            conn,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            if "UPDATE expedientes" in statement:
                raise RuntimeError("fallo de estado")

        event.listen(
            self.engine,
            "before_cursor_execute",
            fallar_estado,
        )
        try:
            with self.assertRaisesRegex(
                RuntimeError,
                "fallo de estado",
            ):
                persistence.guardar(
                    "EXP-1",
                    self._op(),
                    datetime(2026, 7, 29, 12),
                )
        finally:
            event.remove(
                self.engine,
                "before_cursor_execute",
                fallar_estado,
            )

        with self.factory() as session:
            documentos = session.scalar(
                select(func.count()).select_from(DocumentoModel)
            )
        self.assertEqual(documentos, 0)
        self.assertIsNotNone(self.repository.obtener_vigente("EXP-1"))
        self.assertEqual(
            self._estado_expediente(),
            EstadoExpediente.VALIDADO.value,
        )

    def test_indice_parcial_compila_para_postgresql_y_sqlite(
        self,
    ) -> None:
        indice = next(
            indice
            for indice in ValidacionAdministrativaModel.__table__.indexes
            if indice.name
            == "uq_validaciones_administrativas_vigente"
        )

        sql_postgres = str(
            CreateIndex(indice).compile(
                dialect=postgresql.dialect()
            )
        )
        sql_sqlite = str(
            CreateIndex(indice).compile(dialect=sqlite.dialect())
        )

        self.assertIn(
            "WHERE fecha_invalidacion IS NULL",
            sql_postgres,
        )
        self.assertIn(
            "WHERE fecha_invalidacion IS NULL",
            sql_sqlite,
        )

    def test_rechaza_metadatos_de_invalidacion_parciales(self) -> None:
        with self.assertRaises(ValidationError):
            ValidacionAdministrativaRead.model_validate(
                {
                    **self._validacion().model_dump(),
                    "fecha_invalidacion": datetime(2026, 7, 29, 12),
                }
            )

        with self.factory() as session:
            session.add(
                ValidacionAdministrativaModel(
                    expediente_id="EXP-1",
                    resultado="VALIDADA",
                    usuario="Operador",
                    fecha_validacion=datetime(2026, 7, 29, 10),
                    motivo_observacion=None,
                    estado_expediente="VALIDADO",
                    fecha_invalidacion=datetime(2026, 7, 29, 12),
                    motivo_invalidacion=None,
                    usuario_invalidacion=None,
                    controles=[],
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_migracion_normaliza_actos_existentes(self) -> None:
        modulo = importlib.import_module(
            "migrations.versions."
            "20260729_0012_invalidar_validaciones_y_revalidar"
        )
        engine = create_engine("sqlite+pysqlite:///:memory:")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE validaciones_administrativas ("
                "id INTEGER PRIMARY KEY, "
                "expediente_id VARCHAR(32) NOT NULL, "
                "fecha_validacion DATETIME NOT NULL, "
                "fecha_invalidacion DATETIME NULL, "
                "motivo_invalidacion TEXT NULL, "
                "usuario_invalidacion VARCHAR(255) NULL)"
            )
            connection.exec_driver_sql(
                "CREATE TABLE validacion_controles ("
                "validacion_id INTEGER NOT NULL, "
                "orden INTEGER NOT NULL, "
                "codigo VARCHAR(255) NOT NULL)"
            )
            connection.execute(
                text(
                    "INSERT INTO validaciones_administrativas "
                    "(id, expediente_id, fecha_validacion) VALUES "
                    "(1, 'EXP-1', '2026-07-29 10:00:00'), "
                    "(2, 'EXP-1', '2026-07-29 11:00:00'), "
                    "(3, 'EXP-2', '2026-07-29 12:00:00')"
                )
            )
            connection.exec_driver_sql(
                "INSERT INTO validacion_controles "
                "(validacion_id, orden, codigo) "
                "VALUES (1, 0, 'Original')"
            )

            modulo._normalizar_validaciones_existentes(connection)

            filas = connection.execute(
                text(
                    "SELECT id, fecha_invalidacion, "
                    "motivo_invalidacion, usuario_invalidacion "
                    "FROM validaciones_administrativas ORDER BY id"
                )
            ).mappings().all()
            controles = connection.exec_driver_sql(
                "SELECT validacion_id, orden, codigo "
                "FROM validacion_controles"
            ).all()
        engine.dispose()

        self.assertIsNotNone(filas[0]["fecha_invalidacion"])
        self.assertEqual(
            filas[0]["motivo_invalidacion"],
            "Normalización técnica de vigencia — Sprint 0075 Diff 3",
        )
        self.assertEqual(
            filas[0]["usuario_invalidacion"],
            "MIGRACION_0075",
        )
        self.assertIsNone(filas[1]["fecha_invalidacion"])
        self.assertIsNone(filas[2]["fecha_invalidacion"])
        self.assertEqual(controles, [(1, 0, "Original")])

    def test_downgrade_elimina_indice_restriccion_y_columnas(
        self,
    ) -> None:
        modulo = importlib.import_module(
            "migrations.versions."
            "20260729_0012_invalidar_validaciones_y_revalidar"
        )
        op_mock = MagicMock()

        with patch.object(modulo, "op", op_mock):
            modulo.downgrade()

        op_mock.drop_index.assert_called_once_with(
            "uq_validaciones_administrativas_vigente",
            table_name="validaciones_administrativas",
        )
        op_mock.drop_constraint.assert_called_once_with(
            "ck_validaciones_administrativas_invalidacion_completa",
            "validaciones_administrativas",
            type_="check",
        )
        self.assertEqual(op_mock.drop_column.call_count, 3)

    def _guardar_expediente(self) -> None:
        PostgresExpedienteRepository(self.factory).guardar(
            Expediente(
                id="EXP-1",
                numero_interno="033-1/2026",
                numero_gdeba=None,
                solicitud_intervencion_id=None,
                decision_administrativa_id=None,
                configuracion_uc_id=None,
                id_suna=None,
                tipo_tramite="FONDO_COMPENSADOR",
                estado=EstadoExpediente.BORRADOR,
                establecimiento="EP 1",
                objeto="Objeto",
                numero_disposicion=None,
                creado=datetime(2026, 7, 29, 9),
            )
        )

    def _validacion(
        self,
        *,
        fecha: datetime = datetime(2026, 7, 29, 10),
        usuario: str = "Secretario Técnico",
        resultado: str = "VALIDADA",
        motivo_observacion: str | None = None,
    ) -> ValidacionAdministrativaRead:
        return ValidacionAdministrativaRead(
            expediente_id="EXP-1",
            resultado=resultado,
            usuario=usuario,
            fecha_validacion=fecha,
            motivo_observacion=motivo_observacion,
            estado_expediente=EstadoExpediente.VALIDADO.value,
            controles=[
                ControlValidacionSnapshotRead(
                    orden=0,
                    codigo="Expediente interno",
                    estado="OK",
                    observacion="Expediente informado.",
                )
            ],
        )

    @staticmethod
    def _checklist() -> ChecklistFisicoRead:
        return ChecklistFisicoRead(
            expediente_id="EXP-1",
            factura=True,
            remito_conformidad=True,
            cae=True,
            arca=True,
            arba=False,
            observaciones="Checklist modificado",
            usuario="Operador checklist",
            fecha=datetime(2026, 7, 29, 12),
        )

    @staticmethod
    def _op() -> DocumentoCreate:
        return DocumentoCreate(
            tipo="OP",
            nombre_archivo="op.pdf",
            ruta="storage/expedientes/EXP-1/op.pdf",
            observaciones=None,
            tamano_bytes=100,
            mime_type="application/pdf",
        )

    def _estado_expediente(self) -> str:
        with self.factory() as session:
            return session.scalar(
                select(ExpedienteModel.estado).where(
                    ExpedienteModel.id == "EXP-1"
                )
            )


if __name__ == "__main__":
    unittest.main()
