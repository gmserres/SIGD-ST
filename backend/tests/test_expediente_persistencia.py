import unittest
from datetime import datetime
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.expediente_mapper import a_dominio, a_modelo
from app.infrastructure.database.repositories.expediente_postgres_repository import (
    PostgresExpedienteRepository,
)
from app.repositories.expediente_in_memory_repository import (
    InMemoryExpedienteRepository,
)
from app.schemas.expediente import ExpedienteCreate, ExpedienteUpdate
from app.services.expedientes import (
    ConfiguracionUCExpedienteYaAsociadaError,
    EscrituraNumeroDisposicionLegacyDeshabilitadaError,
    ExpedienteService,
)


class ExpedientePersistenciaTest(unittest.TestCase):
    def test_servicio_delega_en_repositorio_y_conserva_contratos(self) -> None:
        repository = InMemoryExpedienteRepository()
        servicio = ExpedienteService(repository)

        primero = servicio.crear(self._crear_data("033-1/2026"))
        segundo = servicio.crear(self._crear_data("033-2/2026"))

        self.assertEqual(primero.id, "EXP-000001")
        self.assertEqual(segundo.id, "EXP-000002")
        self.assertEqual([item.id for item in servicio.listar()], [primero.id, segundo.id])
        self.assertEqual(servicio.obtener(primero.id), primero)
        self.assertIsNone(primero.configuracion_uc_id)

    def test_asocia_configuracion_uc_y_conserva_el_agregado(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))

        asociado = servicio.asociar_configuracion_uc(
            creado.id,
            "configuracion-1",
        )

        self.assertEqual(asociado.configuracion_uc_id, "configuracion-1")
        self.assertEqual(asociado.estado, creado.estado)
        self.assertEqual(asociado.numero_interno, creado.numero_interno)
        self.assertEqual(asociado.creado, creado.creado)

    def test_asociacion_repetida_es_idempotente(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))
        servicio.asociar_configuracion_uc(creado.id, "configuracion-1")

        repetido = servicio.asociar_configuracion_uc(
            creado.id,
            "configuracion-1",
        )

        self.assertEqual(repetido.configuracion_uc_id, "configuracion-1")

    def test_rechaza_reemplazar_configuracion_uc(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))
        servicio.asociar_configuracion_uc(creado.id, "configuracion-1")

        with self.assertRaises(
            ConfiguracionUCExpedienteYaAsociadaError
        ) as contexto:
            servicio.asociar_configuracion_uc(
                creado.id,
                "configuracion-2",
            )

        self.assertEqual(contexto.exception.expediente_id, creado.id)
        self.assertEqual(
            contexto.exception.configuracion_uc_id_existente,
            "configuracion-1",
        )
        self.assertEqual(
            contexto.exception.configuracion_uc_id_solicitada,
            "configuracion-2",
        )

    def test_actualizacion_generica_no_borra_ni_reemplaza_asociacion(
        self,
    ) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))
        servicio.asociar_configuracion_uc(creado.id, "configuracion-1")

        data = ExpedienteUpdate.model_validate(
            {
                "establecimiento": "EP 2",
                "configuracion_uc_id": "configuracion-2",
            }
        )
        actualizado = servicio.actualizar(creado.id, data)

        self.assertNotIn(
            "configuracion_uc_id",
            ExpedienteUpdate.model_fields,
        )
        self.assertEqual(
            actualizado.configuracion_uc_id,
            "configuracion-1",
        )

    def test_actualiza_campos_y_preserva_identidad_relaciones_fecha_y_estado(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))

        actualizado = servicio.actualizar(
            creado.id,
            ExpedienteUpdate(
                establecimiento="EP 2",
            ),
        )

        self.assertEqual(actualizado.id, creado.id)
        self.assertEqual(actualizado.solicitud_intervencion_id, creado.solicitud_intervencion_id)
        self.assertEqual(actualizado.decision_administrativa_id, creado.decision_administrativa_id)
        self.assertEqual(actualizado.creado, creado.creado)
        self.assertEqual(actualizado.estado, creado.estado)
        self.assertIsNone(actualizado.numero_disposicion)

    def test_rechaza_escribir_numero_disposicion_legacy(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))

        with self.assertRaises(
            EscrituraNumeroDisposicionLegacyDeshabilitadaError
        ):
            servicio.actualizar(
                creado.id,
                ExpedienteUpdate(numero_disposicion="10/2026"),
            )

        self.assertIsNone(servicio.obtener(creado.id).numero_disposicion)

    def test_rechaza_crear_con_numero_disposicion_legacy(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        data = self._crear_data("033-1/2026").model_copy(
            update={"numero_disposicion": "10/2026"}
        )

        with self.assertRaises(
            EscrituraNumeroDisposicionLegacyDeshabilitadaError
        ):
            servicio.crear(data)

    def test_cambia_estado_y_rechaza_expediente_inexistente(self) -> None:
        servicio = ExpedienteService(InMemoryExpedienteRepository())
        creado = servicio.crear(self._crear_data("033-1/2026"))

        actualizado = servicio.cambiar_estado(creado.id, EstadoExpediente.VALIDADO)

        self.assertEqual(actualizado.estado, EstadoExpediente.VALIDADO)
        with self.assertRaises(KeyError):
            servicio.obtener("EXP-INEXISTENTE")

    def test_mapper_preserva_todos_los_campos(self) -> None:
        expediente = self._crear_dominio(
            "EXP-000001",
            configuracion_uc_id="configuracion-1",
        )

        recuperado = a_dominio(a_modelo(expediente))

        self.assertEqual(recuperado, expediente)

    def test_repositorio_relacional_persiste_entre_sesiones_y_reconstrucciones(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)
        fabrica = sessionmaker(bind=engine, expire_on_commit=False)
        primero = PostgresExpedienteRepository(fabrica)
        expediente = self._crear_dominio(
            "EXP-000001",
            configuracion_uc_id="configuracion-1",
        )

        primero.guardar(expediente)
        segundo = PostgresExpedienteRepository(fabrica)

        self.assertEqual(segundo.obtener_por_id(expediente.id), expediente)
        self.assertEqual(segundo.listar(), [expediente])

    def test_repositorio_hace_rollback_ante_error(self) -> None:
        sesion = MagicMock()
        sesion.scalar.return_value = None
        sesion.commit.side_effect = RuntimeError("Error controlado")
        fabrica = MagicMock()
        fabrica.return_value.__enter__.return_value = sesion
        repository = PostgresExpedienteRepository(fabrica)
        expediente = self._crear_dominio("EXP-000001")

        with self.assertRaisesRegex(RuntimeError, "Error controlado"):
            repository.guardar(expediente)

        sesion.rollback.assert_called_once_with()

    @staticmethod
    def _crear_data(
        numero_interno: str,
        configuracion_uc_id: str | None = None,
    ) -> ExpedienteCreate:
        return ExpedienteCreate(
            numero_interno=numero_interno,
            numero_gdeba=None,
            solicitud_intervencion_id="solicitud-1",
            decision_administrativa_id="decision-1",
            configuracion_uc_id=configuracion_uc_id,
            id_suna="123",
            tipo_tramite="FONDO_COMPENSADOR",
            establecimiento="EP 1",
            objeto="OBJETO",
            numero_disposicion=None,
        )

    @staticmethod
    def _crear_dominio(
        expediente_id: str,
        configuracion_uc_id: str | None = None,
    ) -> Expediente:
        return Expediente(
            id=expediente_id,
            numero_interno="033-1/2026",
            numero_gdeba=None,
            solicitud_intervencion_id="solicitud-1",
            decision_administrativa_id="decision-1",
            configuracion_uc_id=configuracion_uc_id,
            id_suna="123",
            tipo_tramite="FONDO_COMPENSADOR",
            estado=EstadoExpediente.BORRADOR,
            establecimiento="EP 1",
            objeto="OBJETO",
            numero_disposicion=None,
            creado=datetime(2026, 7, 22, 10, 0),
        )


if __name__ == "__main__":
    unittest.main()
