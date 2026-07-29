import unittest
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.api.expedientes import (
    guardar_checklist_fisico,
    obtener_checklist_fisico,
)
from app.domain.estados import EstadoExpediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.checklist_fisico_mapper import (
    a_modelo,
    a_schema,
)
from app.infrastructure.database.models.checklist_fisico_model import (
    ChecklistFisicoModel,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.repositories.checklist_fisico_postgres_repository import (
    PostgresChecklistFisicoRepository,
)
from app.schemas.checklist_fisico import (
    ChecklistFisicoCreate,
    ChecklistFisicoRead,
)
from app.services.checklist_fisico import ChecklistFisicoService


class ChecklistFisicoPersistenciaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self._guardar_expediente("EXP-1")
        self.repository = PostgresChecklistFisicoRepository(
            self.factory
        )

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_mapper_conserva_todos_los_campos(self) -> None:
        checklist = self._checklist()
        modelo = a_modelo(checklist)

        self.assertEqual(a_schema(modelo), checklist)

    def test_inexistente_devuelve_none(self) -> None:
        self.assertIsNone(
            self.repository.obtener_por_expediente("EXP-1")
        )

    def test_guarda_y_recupera_todos_los_campos(self) -> None:
        checklist = self._checklist()

        guardado = self.repository.guardar(checklist)

        self.assertEqual(guardado, checklist)
        self.assertEqual(
            self.repository.obtener_por_expediente("EXP-1"),
            checklist,
        )

    def test_actualiza_sin_crear_segunda_fila(self) -> None:
        self.repository.guardar(self._checklist())
        actualizado = self._checklist(
            factura=False,
            cae=False,
            observaciones="Checklist actualizado",
            usuario="Otro operador",
            fecha=datetime(2026, 7, 29, 13),
        )

        resultado = self.repository.guardar(actualizado)

        self.assertEqual(resultado, actualizado)
        self.assertEqual(
            self.repository.obtener_por_expediente("EXP-1"),
            actualizado,
        )
        with self.factory() as session:
            cantidad = session.scalar(
                select(func.count())
                .select_from(ChecklistFisicoModel)
                .where(
                    ChecklistFisicoModel.expediente_id == "EXP-1"
                )
            )
        self.assertEqual(cantidad, 1)

    def test_restriccion_unica_rechaza_segunda_fila(self) -> None:
        with self.factory() as session:
            session.add(a_modelo(self._checklist()))
            session.commit()

        with self.factory() as session:
            session.add(a_modelo(self._checklist()))
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_servicio_nuevo_recupera_checklist_persistido(self) -> None:
        servicio_a = ChecklistFisicoService(self.repository)
        data = self._data()

        guardado = servicio_a.guardar("EXP-1", data)
        servicio_b = ChecklistFisicoService(
            PostgresChecklistFisicoRepository(self.factory)
        )

        self.assertEqual(servicio_b.obtener("EXP-1"), guardado)
        self.assertFalse(hasattr(servicio_b, "_items"))

    def test_servicio_actualiza_fecha_y_conserva_una_fila(self) -> None:
        servicio = ChecklistFisicoService(self.repository)

        with patch(
            "app.services.checklist_fisico.datetime"
        ) as reloj:
            reloj.now.side_effect = [
                datetime(2026, 7, 29, 10),
                datetime(2026, 7, 29, 11),
            ]
            primero = servicio.guardar("EXP-1", self._data())
            segundo = servicio.guardar(
                "EXP-1",
                self._data(observaciones="Actualizado"),
            )

        self.assertEqual(
            primero.fecha,
            datetime(2026, 7, 29, 10),
        )
        self.assertEqual(
            segundo.fecha,
            datetime(2026, 7, 29, 11),
        )
        self.assertEqual(
            self.repository.obtener_por_expediente("EXP-1"),
            segundo,
        )

    def test_api_conserva_get_post_y_actualizacion(self) -> None:
        servicio = ChecklistFisicoService(self.repository)

        with (
            patch(
                "app.api.expedientes.obtener_expediente"
            ),
            patch(
                "app.api.expedientes.checklist_fisico_service",
                servicio,
            ),
        ):
            self.assertIsNone(obtener_checklist_fisico("EXP-1"))
            inicial = guardar_checklist_fisico(
                "EXP-1",
                self._data(),
            )
            self.assertEqual(
                obtener_checklist_fisico("EXP-1"),
                inicial,
            )
            actualizado = guardar_checklist_fisico(
                "EXP-1",
                self._data(
                    factura=False,
                    observaciones="Actualizado por API",
                ),
            )
            self.assertEqual(
                obtener_checklist_fisico("EXP-1"),
                actualizado,
            )

        with self.factory() as session:
            cantidad = session.scalar(
                select(func.count())
                .select_from(ChecklistFisicoModel)
            )
        self.assertEqual(cantidad, 1)

    def _guardar_expediente(self, expediente_id: str) -> None:
        with self.factory() as session:
            session.add(
                ExpedienteModel(
                    id=expediente_id,
                    numero_interno="033-075/2026",
                    numero_gdeba=None,
                    solicitud_intervencion_id=None,
                    decision_administrativa_id=None,
                    configuracion_uc_id=None,
                    id_suna=None,
                    tipo_tramite="FONDO_COMPENSADOR",
                    estado=EstadoExpediente.PENDIENTE_VALIDACION.value,
                    establecimiento="EP 75",
                    objeto="Objeto",
                    numero_disposicion=None,
                    creado=datetime(2026, 7, 29, 9),
                )
            )
            session.commit()

    @staticmethod
    def _data(
        *,
        factura: bool = True,
        observaciones: str | None = "Verificado",
    ) -> ChecklistFisicoCreate:
        return ChecklistFisicoCreate(
            factura=factura,
            remito_conformidad=True,
            cae=True,
            arca=True,
            arba=True,
            observaciones=observaciones,
            usuario="Secretario Técnico",
        )

    @staticmethod
    def _checklist(
        *,
        factura: bool = True,
        cae: bool = True,
        observaciones: str | None = "Verificado",
        usuario: str = "Secretario Técnico",
        fecha: datetime = datetime(2026, 7, 29, 10),
    ) -> ChecklistFisicoRead:
        return ChecklistFisicoRead(
            expediente_id="EXP-1",
            factura=factura,
            remito_conformidad=True,
            cae=cae,
            arca=True,
            arba=True,
            observaciones=observaciones,
            usuario=usuario,
            fecha=fecha,
        )


if __name__ == "__main__":
    unittest.main()
