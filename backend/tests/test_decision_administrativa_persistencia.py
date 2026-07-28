import unittest
from datetime import date
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.decision_administrativa import DecisionAdministrativa
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.decision_administrativa_mapper import (
    a_dominio,
    a_modelo,
)
from app.infrastructure.database.repositories.decision_administrativa_postgres_repository import (
    PostgresDecisionAdministrativaRepository,
)
from app.repositories.decision_administrativa_repository import (
    DecisionAdministrativaYaRegistradaError,
)
from app.schemas.decision_administrativa import DecisionAdministrativaCreate
from app.services.decision_administrativa_service import (
    DecisionAprobatoriaDuplicadaError,
    DecisionAdministrativaService,
)


class DecisionAdministrativaPersistenciaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_persiste_y_reconstruye_exactamente_la_decision(self) -> None:
        decision = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
            fondo_interviniente="FONDO_COMPENSADOR",
        )
        primero = PostgresDecisionAdministrativaRepository(
            self.session_factory
        )

        primero.guardar(decision)
        segundo = PostgresDecisionAdministrativaRepository(
            self.session_factory
        )

        self.assertEqual(
            segundo.obtener_por_id(decision.id_decision),
            decision,
        )

    def test_lista_decisiones_por_solicitud(self) -> None:
        repository = PostgresDecisionAdministrativaRepository(
            self.session_factory
        )
        primera = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
            solicitud_id="solicitud-1",
        )
        segunda = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000002",
            solicitud_id="solicitud-2",
        )
        repository.guardar(primera)
        repository.guardar(segunda)

        recuperadas = repository.listar(
            solicitud_intervencion_id="solicitud-1",
        )

        self.assertEqual(recuperadas, [primera])
        self.assertCountEqual(repository.listar(), [primera, segunda])

    def test_rechaza_guardar_dos_veces_el_mismo_id_sin_sobrescribir(
        self,
    ) -> None:
        repository = PostgresDecisionAdministrativaRepository(
            self.session_factory
        )
        original = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
            resultado="Rechazar intervención",
            fondo_interviniente=None,
        )
        reemplazo = self._crear_dominio(
            decision_id=original.id_decision,
            resultado="Aprobar intervención",
            fondo_interviniente="FONDO_COMPENSADOR",
        )
        repository.guardar(original)

        with self.assertRaises(DecisionAdministrativaYaRegistradaError):
            repository.guardar(reemplazo)

        self.assertEqual(
            repository.obtener_por_id(original.id_decision),
            original,
        )

    def test_listado_tiene_orden_estable_por_fecha_e_id(self) -> None:
        repository = PostgresDecisionAdministrativaRepository(
            self.session_factory
        )
        posterior = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000003",
            fecha_decision=date(2026, 7, 28),
        )
        segundo_misma_fecha = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000002",
            fecha_decision=date(2026, 7, 27),
        )
        primero_misma_fecha = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
            fecha_decision=date(2026, 7, 27),
        )
        repository.guardar(posterior)
        repository.guardar(segundo_misma_fecha)
        repository.guardar(primero_misma_fecha)

        self.assertEqual(
            repository.listar(),
            [
                primero_misma_fecha,
                segundo_misma_fecha,
                posterior,
            ],
        )

    def test_mapper_conserva_campos_opcionales_ausentes(self) -> None:
        decision = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
            resultado="Solicitar información adicional",
            fondo_interviniente=None,
            descripcion_fondo=None,
        )

        recuperada = a_dominio(a_modelo(decision))

        self.assertEqual(recuperada, decision)
        self.assertIsNone(recuperada.fondo_interviniente)
        self.assertIsNone(recuperada.descripcion_fondo)

    def test_mapper_conserva_fondo_otro_y_descripcion(self) -> None:
        decision = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
            fondo_interviniente="OTRO",
            descripcion_fondo="Programa específico",
        )

        recuperada = a_dominio(a_modelo(decision))

        self.assertEqual(recuperada.fondo_interviniente, "OTRO")
        self.assertEqual(
            recuperada.descripcion_fondo,
            "Programa específico",
        )

    def test_servicio_conserva_aprobacion_de_fondo_compensador(
        self,
    ) -> None:
        servicio = DecisionAdministrativaService(
            PostgresDecisionAdministrativaRepository(
                self.session_factory
            )
        )

        decision = servicio.crear(self._crear_data())

        self.assertEqual(
            decision.fondo_interviniente,
            "FONDO_COMPENSADOR",
        )
        self.assertEqual(decision.autoridad_decisora, "Tesorero")
        self.assertEqual(
            decision.usuario_registrante,
            "Secretario Técnico",
        )

    def test_bloquea_segunda_aprobacion_tras_reconstruir_servicio(
        self,
    ) -> None:
        primero = DecisionAdministrativaService(
            PostgresDecisionAdministrativaRepository(
                self.session_factory
            )
        )
        primero.crear(self._crear_data())
        segundo = DecisionAdministrativaService(
            PostgresDecisionAdministrativaRepository(
                self.session_factory
            )
        )

        with self.assertRaisesRegex(
            DecisionAprobatoriaDuplicadaError,
            "La intervención ya fue aprobada.",
        ):
            segundo.crear(self._crear_data())

    def test_repositorio_hace_rollback_ante_error(self) -> None:
        sesion = MagicMock()
        sesion.get.return_value = None
        sesion.commit.side_effect = RuntimeError("Error controlado")
        fabrica = MagicMock()
        fabrica.return_value.__enter__.return_value = sesion
        repository = PostgresDecisionAdministrativaRepository(fabrica)
        decision = self._crear_dominio(
            decision_id="00000000-0000-0000-0000-000000000001",
        )

        with self.assertRaisesRegex(RuntimeError, "Error controlado"):
            repository.guardar(decision)

        sesion.rollback.assert_called_once_with()

    @staticmethod
    def _crear_data() -> DecisionAdministrativaCreate:
        return DecisionAdministrativaCreate(
            solicitud_intervencion_id="solicitud-1",
            autoridad_decisora="Tesorero",
            fecha_decision=date(2026, 7, 27),
            resultado="Aprobar intervención",
            fundamento="Intervención aprobada.",
            fondo_interviniente="FONDO_COMPENSADOR",
            usuario_registrante="Secretario Técnico",
        )

    @staticmethod
    def _crear_dominio(
        decision_id: str,
        solicitud_id: str = "solicitud-1",
        resultado: str = "Aprobar intervención",
        fecha_decision: date = date(2026, 7, 27),
        fondo_interviniente: str | None = "FONDO_COMPENSADOR",
        descripcion_fondo: str | None = None,
    ) -> DecisionAdministrativa:
        return DecisionAdministrativa(
            id_decision=decision_id,
            solicitud_intervencion_id=solicitud_id,
            autoridad_decisora="Tesorero",
            fecha_decision=fecha_decision,
            resultado=resultado,
            fundamento="Fundamento",
            fondo_interviniente=fondo_interviniente,
            descripcion_fondo=descripcion_fondo,
            usuario_registrante="Secretario Técnico",
        )


if __name__ == "__main__":
    unittest.main()
