import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from app.api.expedientes import (
    validar_expediente,
    validar_expediente_con_observaciones,
)
from app.composition.validacion import validacion_service
from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.models.validacion_administrativa_model import (
    ValidacionAdministrativaModel,
    ValidacionControlModel,
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
from app.schemas.expediente import ExpedienteRead
from app.schemas.validacion import (
    ControlValidacion,
    ControlValidacionSnapshotRead,
    ValidacionAdministrativaRead,
    ValidacionExpedienteRead,
)
from app.schemas.validacion_observada import ValidacionObservadaCreate
from app.services.validaciones import ValidacionService


class ValidacionAdministrativaPersistenciaTest(unittest.TestCase):
    """SQLite no valida el bloqueo real de SELECT FOR UPDATE."""

    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self.repository = PostgresValidacionAdministrativaRepository(
            self.factory
        )
        self.persistence = PostgresValidarExpedientePersistence(
            self.factory
        )
        self._guardar_expediente()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_registra_validacion_normal_con_snapshot_ordenado(self) -> None:
        expediente, acto = self.persistence.validar(
            self._acto("VALIDADA")
        )

        self.assertEqual(expediente.estado, EstadoExpediente.VALIDADO)
        self.assertIsNotNone(acto.id)
        self.assertEqual(acto.resultado, "VALIDADA")
        self.assertEqual(acto.usuario, "Secretario Técnico")
        self.assertEqual(
            acto.fecha_validacion,
            datetime(2026, 7, 29, 14, 0),
        )
        self.assertIsNone(acto.motivo_observacion)
        self.assertEqual(acto.estado_expediente, "VALIDADO")
        self.assertEqual(
            [control.codigo for control in acto.controles],
            ["Expediente interno", "Establecimiento", "Objeto"],
        )
        self.assertEqual(
            [control.orden for control in acto.controles],
            [0, 1, 2],
        )

    def test_registra_validacion_con_observaciones_y_motivo(self) -> None:
        _, acto = self.persistence.validar(
            self._acto(
                "VALIDADA_CON_OBSERVACIONES",
                motivo="  Documentación física verificada.  ",
            )
        )

        self.assertEqual(
            acto.resultado,
            "VALIDADA_CON_OBSERVACIONES",
        )
        self.assertEqual(
            acto.motivo_observacion,
            "Documentación física verificada.",
        )

    def test_segunda_validacion_no_modifica_primer_snapshot(self) -> None:
        _, primera = self.persistence.validar(self._acto("VALIDADA"))
        segunda_data = self._acto(
            "VALIDADA_CON_OBSERVACIONES",
            motivo="Se continúa con observaciones.",
            fecha=datetime(2026, 7, 29, 15, 0),
        )
        segunda_data.controles[0].estado = "ADVERTENCIA"
        segunda_data.controles[0].observacion = "Control actualizado."
        _, segunda = self.persistence.validar(segunda_data)

        actos = self.repository.listar_por_expediente("EXP-1")
        self.assertEqual([acto.id for acto in actos], [primera.id, segunda.id])
        self.assertEqual(actos[0].controles[0].estado, "OK")
        self.assertEqual(
            actos[0].controles[0].observacion,
            "Expediente informado.",
        )
        self.assertEqual(
            actos[1].controles[0].estado,
            "ADVERTENCIA",
        )

    def test_recupera_ultima_validacion_con_otro_servicio(self) -> None:
        self.persistence.validar(self._acto("VALIDADA"))
        self.persistence.validar(
            self._acto(
                "VALIDADA_CON_OBSERVACIONES",
                motivo="Motivo de la segunda validación.",
                fecha=datetime(2026, 7, 29, 15, 0),
            )
        )

        servicio_nuevo = ValidacionService(
            repository=PostgresValidacionAdministrativaRepository(
                self.factory
            )
        )
        recuperada = servicio_nuevo.obtener_ultima("EXP-1")

        self.assertIsNotNone(recuperada)
        self.assertEqual(
            recuperada.resultado,
            "VALIDADA_CON_OBSERVACIONES",
        )
        self.assertEqual(len(recuperada.controles), 3)

    def test_desempata_ultima_validacion_por_pk(self) -> None:
        fecha = datetime(2026, 7, 29, 14, 0)
        primera = self.repository.registrar(
            self._acto("VALIDADA", fecha=fecha)
        )
        segunda = self.repository.registrar(
            self._acto("VALIDADA", fecha=fecha)
        )

        ultima = self.repository.obtener_ultima_por_expediente("EXP-1")

        self.assertEqual(ultima.id, segunda.id)
        self.assertGreater(segunda.id, primera.id)

    def test_reglas_de_motivo(self) -> None:
        normal = self._acto(
            "VALIDADA",
            motivo="Este motivo debe descartarse.",
        )
        self.assertIsNone(normal.motivo_observacion)

        with self.assertRaises(ValidationError):
            self._acto(
                "VALIDADA_CON_OBSERVACIONES",
                motivo="   ",
            )

    def test_un_flush_un_commit_en_operacion_coordinada(self) -> None:
        session = MagicMock()
        session.scalar.return_value = self._modelo_expediente_mock()
        factory = MagicMock()
        factory.return_value.__enter__.return_value = session

        PostgresValidarExpedientePersistence(factory).validar(
            self._acto("VALIDADA")
        )

        session.flush.assert_called_once_with()
        session.commit.assert_called_once_with()
        session.rollback.assert_not_called()

    def test_servicio_copia_todos_los_controles_actuales(self) -> None:
        persistence = MagicMock()
        expediente = self._expediente_dominio(
            estado=EstadoExpediente.VALIDADO
        )
        persistence.validar.side_effect = (
            lambda validacion: (expediente, validacion)
        )
        servicio = ValidacionService(persistence=persistence)
        nombres = [
            "Expediente interno",
            "Establecimiento",
            "Objeto",
            "Facturas",
            "Remito o conformidad",
            "Validación CAE",
            "Constancia ARCA",
            "Certificado ARBA",
        ]
        calculada = ValidacionExpedienteRead(
            expediente_id="EXP-1",
            estado_general="VERDE",
            errores=[],
            advertencias=[],
            controles=[
                ControlValidacion(
                    control=nombre,
                    estado="OK",
                    observacion=f"{nombre} acreditado.",
                )
                for nombre in nombres
            ],
        )

        resultado = servicio.registrar(
            validacion_calculada=calculada,
            resultado="VALIDADA",
            usuario="Operador",
        )

        self.assertEqual(resultado.estado, EstadoExpediente.VALIDADO)
        acto = persistence.validar.call_args.args[0]
        self.assertEqual(
            [control.codigo for control in acto.controles],
            nombres,
        )
        self.assertEqual(
            [control.orden for control in acto.controles],
            list(range(8)),
        )

    def test_rollback_sin_parciales_ante_fallos_de_escritura(self) -> None:
        casos = (
            "INSERT INTO validaciones_administrativas",
            "INSERT INTO validacion_controles",
            "UPDATE expedientes",
        )
        for sentencia_objetivo in casos:
            with self.subTest(sentencia=sentencia_objetivo):
                self._limpiar_validaciones_y_restaurar_estado()

                def fallar(
                    conn,
                    cursor,
                    statement,
                    parameters,
                    context,
                    executemany,
                ):
                    if sentencia_objetivo in statement:
                        raise RuntimeError("fallo de escritura")

                event.listen(
                    self.engine,
                    "before_cursor_execute",
                    fallar,
                )
                try:
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "fallo de escritura",
                    ):
                        self.persistence.validar(
                            self._acto("VALIDADA")
                        )
                finally:
                    event.remove(
                        self.engine,
                        "before_cursor_execute",
                        fallar,
                    )

                with self.factory() as session:
                    expediente = session.get(ExpedienteModel, 1)
                    actos = session.scalar(
                        select(func.count()).select_from(
                            ValidacionAdministrativaModel
                        )
                    )
                    controles = session.scalar(
                        select(func.count()).select_from(
                            ValidacionControlModel
                        )
                    )
                self.assertEqual(
                    expediente.estado,
                    EstadoExpediente.BORRADOR.value,
                )
                self.assertEqual(actos, 0)
                self.assertEqual(controles, 0)

    def test_endpoint_no_registra_si_validacion_funcional_falla(self) -> None:
        calculada = self._calculada(
            errores=["Falta número de expediente interno."],
        )
        with (
            patch(
                "app.api.expedientes.obtener_expediente",
                return_value=self._expediente_read(),
            ),
            patch.object(
                validacion_service,
                "validar",
                return_value=calculada,
            ),
            patch.object(
                validacion_service,
                "registrar",
            ) as registrar,
        ):
            with self.assertRaises(HTTPException) as contexto:
                validar_expediente("EXP-1")

        self.assertEqual(contexto.exception.status_code, 409)
        registrar.assert_not_called()

    def test_endpoints_conservan_respuesta_y_argumentos(self) -> None:
        expediente = self._expediente_read(
            estado=EstadoExpediente.VALIDADO
        )
        calculada_normal = self._calculada()
        with (
            patch(
                "app.api.expedientes.obtener_expediente",
                return_value=self._expediente_read(),
            ),
            patch.object(
                validacion_service,
                "validar",
                return_value=calculada_normal,
            ),
            patch.object(
                validacion_service,
                "registrar",
                return_value=expediente,
            ) as registrar,
        ):
            respuesta = validar_expediente("EXP-1")

        self.assertEqual(respuesta, expediente)
        registrar.assert_called_once_with(
            validacion_calculada=calculada_normal,
            resultado="VALIDADA",
            usuario="Secretario Técnico",
        )

        calculada_observada = self._calculada(
            advertencias=["Falta acreditar ARBA."],
        )
        data = ValidacionObservadaCreate(
            motivo="Se continúa con documentación pendiente.",
            usuario="Operador",
        )
        with (
            patch(
                "app.api.expedientes.obtener_expediente",
                return_value=self._expediente_read(),
            ),
            patch.object(
                validacion_service,
                "validar",
                return_value=calculada_observada,
            ),
            patch.object(
                validacion_service,
                "registrar",
                return_value=expediente,
            ) as registrar,
        ):
            respuesta = validar_expediente_con_observaciones(
                "EXP-1",
                data,
            )

        self.assertEqual(respuesta, expediente)
        registrar.assert_called_once_with(
            validacion_calculada=calculada_observada,
            resultado="VALIDADA_CON_OBSERVACIONES",
            usuario="Operador",
            motivo_observacion=data.motivo,
        )

    def _guardar_expediente(self) -> None:
        PostgresExpedienteRepository(self.factory).guardar(
            self._expediente_dominio()
        )

    def _acto(
        self,
        resultado,
        motivo=None,
        fecha=None,
    ) -> ValidacionAdministrativaRead:
        return ValidacionAdministrativaRead(
            expediente_id="EXP-1",
            resultado=resultado,
            usuario="Secretario Técnico",
            fecha_validacion=fecha or datetime(2026, 7, 29, 14, 0),
            motivo_observacion=motivo,
            estado_expediente=EstadoExpediente.VALIDADO.value,
            controles=[
                ControlValidacionSnapshotRead(
                    orden=0,
                    codigo="Expediente interno",
                    estado="OK",
                    observacion="Expediente informado.",
                ),
                ControlValidacionSnapshotRead(
                    orden=1,
                    codigo="Establecimiento",
                    estado="OK",
                    observacion="Establecimiento informado.",
                ),
                ControlValidacionSnapshotRead(
                    orden=2,
                    codigo="Objeto",
                    estado="OK",
                    observacion="Objeto informado.",
                ),
            ],
        )

    @staticmethod
    def _calculada(
        errores=None,
        advertencias=None,
    ) -> ValidacionExpedienteRead:
        return ValidacionExpedienteRead(
            expediente_id="EXP-1",
            estado_general=(
                "ROJO"
                if errores
                else ("AMARILLO" if advertencias else "VERDE")
            ),
            errores=errores or [],
            advertencias=advertencias or [],
            controles=[
                ControlValidacion(
                    control="Expediente interno",
                    estado="OK",
                    observacion="Expediente informado.",
                )
            ],
        )

    @staticmethod
    def _expediente_read(
        estado=EstadoExpediente.BORRADOR,
    ) -> ExpedienteRead:
        return ExpedienteRead(
            id="EXP-1",
            numero_interno="033-1/2026",
            numero_gdeba=None,
            solicitud_intervencion_id="SOL-1",
            decision_administrativa_id="DEC-1",
            configuracion_uc_id=None,
            id_suna="1",
            tipo_tramite="FONDO_COMPENSADOR",
            estado=estado,
            establecimiento="EP 1",
            objeto="Objeto",
            numero_disposicion=None,
            creado=datetime(2026, 7, 29, 13, 0),
        )

    @staticmethod
    def _expediente_dominio(
        estado=EstadoExpediente.BORRADOR,
    ) -> Expediente:
        return Expediente(
            id="EXP-1",
            numero_interno="033-1/2026",
            numero_gdeba=None,
            solicitud_intervencion_id="SOL-1",
            decision_administrativa_id="DEC-1",
            configuracion_uc_id=None,
            id_suna="1",
            tipo_tramite="FONDO_COMPENSADOR",
            estado=estado,
            establecimiento="EP 1",
            objeto="Objeto",
            numero_disposicion=None,
            creado=datetime(2026, 7, 29, 13, 0),
        )

    @staticmethod
    def _modelo_expediente_mock():
        modelo = MagicMock()
        modelo.id = "EXP-1"
        modelo.numero_interno = "033-1/2026"
        modelo.numero_gdeba = None
        modelo.solicitud_intervencion_id = "SOL-1"
        modelo.decision_administrativa_id = "DEC-1"
        modelo.configuracion_uc_id = None
        modelo.id_suna = "1"
        modelo.tipo_tramite = "FONDO_COMPENSADOR"
        modelo.estado = EstadoExpediente.BORRADOR.value
        modelo.establecimiento = "EP 1"
        modelo.objeto = "Objeto"
        modelo.numero_disposicion = None
        modelo.creado = datetime(2026, 7, 29, 13, 0)
        return modelo

    def _limpiar_validaciones_y_restaurar_estado(self) -> None:
        with self.factory() as session:
            session.query(ValidacionControlModel).delete()
            session.query(ValidacionAdministrativaModel).delete()
            expediente = session.get(ExpedienteModel, 1)
            expediente.estado = EstadoExpediente.BORRADOR.value
            session.commit()


if __name__ == "__main__":
    unittest.main()
