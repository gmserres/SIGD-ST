import unittest
from datetime import date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.domain.control_proveedor_op import EstadoControlProveedorOP
from app.domain.control_proveedor_op_evidencia import (
    ControlProveedorOPEvidencia,
)
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.control_proveedor_op_model import (
    ControlProveedorOPModel,
)
from app.infrastructure.database.models.decision_administrativa_model import (
    DecisionAdministrativaModel,
)
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.proveedor_model import ProveedorModel
from app.infrastructure.database.models.seleccion_proveedor_model import (
    SeleccionProveedorModel,
)
from app.infrastructure.database.models.solicitud_intervencion_model import (
    SolicitudIntervencionModel,
)
from app.infrastructure.database.repositories.control_proveedor_op_postgres_repository import (
    PostgresControlProveedorOPRepository,
)


EXPEDIENTE_ID = "EXP-000001"
SOLICITUD_ID = "00000000-0000-0000-0000-000000000201"
DECISION_ID = "00000000-0000-0000-0000-000000000301"
PROVEEDOR_A_ID = "00000000-0000-0000-0000-000000000401"
PROVEEDOR_B_ID = "00000000-0000-0000-0000-000000000402"
SELECCION_A_ID = "00000000-0000-0000-0000-000000000101"
SELECCION_B_ID = "00000000-0000-0000-0000-000000000102"
CONTROL_A_ID = "00000000-0000-0000-0000-000000000501"
CONTROL_B_ID = "00000000-0000-0000-0000-000000000502"


class ControlProveedorOPPersistenciaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")

        @event.listens_for(self.engine, "connect")
        def habilitar_fks(conexion, _registro):
            cursor = conexion.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self.repository = PostgresControlProveedorOPRepository(
            self.session_factory
        )
        self._crear_dependencias()

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_persiste_coincide(self) -> None:
        control = self._control()
        guardado = self.repository.guardar(control)

        self.assertEqual(guardado, control)
        self.assertEqual(
            self.repository.obtener_por_id(control.id_control), control
        )

    def test_persiste_cuit_diferente(self) -> None:
        recuperado = self.repository.guardar(
            self._control(
                estado=EstadoControlProveedorOP.CUIT_DIFERENTE,
                cuit_detectado="30000000007",
            )
        )

        self.assertEqual(
            recuperado.estado, EstadoControlProveedorOP.CUIT_DIFERENTE
        )
        self.assertEqual(recuperado.cuit_detectado, "30000000007")

    def test_persiste_no_verificable(self) -> None:
        recuperado = self.repository.guardar(
            self._control(
                estado=EstadoControlProveedorOP.NO_VERIFICABLE,
                cuit_detectado=None,
            )
        )

        self.assertEqual(
            recuperado.estado, EstadoControlProveedorOP.NO_VERIFICABLE
        )
        self.assertIsNone(recuperado.cuit_detectado)

    def test_preserva_snapshot_seleccionado(self) -> None:
        recuperado = self.repository.guardar(
            self._control(
                proveedor_razon_social_seleccionada=(
                    "Proveedor Histórico S.R.L."
                )
            )
        )

        self.assertEqual(
            recuperado.proveedor_cuit_seleccionado, "30718078063"
        )
        self.assertEqual(
            recuperado.proveedor_razon_social_seleccionada,
            "Proveedor Histórico S.R.L.",
        )

    def test_preserva_snapshot_detectado(self) -> None:
        recuperado = self.repository.guardar(
            self._control(
                razon_social_detectada="Proveedor detectado S.R.L.",
                advertencias=("Advertencia documental.",),
            )
        )

        self.assertEqual(recuperado.cuit_detectado, "30718078063")
        self.assertEqual(
            recuperado.razon_social_detectada,
            "Proveedor detectado S.R.L.",
        )
        self.assertEqual(
            recuperado.advertencias, ("Advertencia documental.",)
        )

    def test_reemplazo_posterior_no_altera_control(self) -> None:
        original = self.repository.guardar(self._control())
        self._reemplazar_seleccion()

        recuperado = self.repository.obtener_por_id(original.id_control)

        self.assertEqual(recuperado, original)

    def test_modificacion_maestro_no_altera_control(self) -> None:
        original = self.repository.guardar(self._control())
        with self.session_factory() as session:
            proveedor = session.get(ProveedorModel, PROVEEDOR_A_ID)
            proveedor.razon_social = "Razón posterior"
            proveedor.activo = False
            session.commit()

        recuperado = self.repository.obtener_por_id(original.id_control)

        self.assertEqual(recuperado, original)

    def test_misma_op_admite_selecciones_a_y_b(self) -> None:
        self.repository.guardar(self._control())
        self._reemplazar_seleccion()
        self.repository.guardar(
            self._control(
                id_control=CONTROL_B_ID,
                seleccion_proveedor_id=SELECCION_B_ID,
                proveedor_cuit_seleccionado="30000000007",
                proveedor_razon_social_seleccionada="Proveedor B",
            )
        )

        historial = self.repository.listar_por_documento("DOC-000001")

        self.assertEqual(
            [item.seleccion_proveedor_id for item in historial],
            [SELECCION_A_ID, SELECCION_B_ID],
        )

    def test_conserva_fecha_y_modo(self) -> None:
        fecha = datetime(2026, 8, 11, 15, 30)
        recuperado = self.repository.guardar(
            self._control(fecha_control=fecha, modo_analisis="MODO-1")
        )

        self.assertEqual(recuperado.fecha_control, fecha)
        self.assertEqual(recuperado.modo_analisis, "MODO-1")

    def test_rechaza_fks_invalidas(self) -> None:
        casos = (
            {"expediente_id": "EXP-INEXISTENTE"},
            {"documento_op_id": "DOC-999999"},
            {
                "solicitud_intervencion_id":
                "00000000-0000-0000-0000-999999999999"
            },
            {
                "seleccion_proveedor_id":
                "00000000-0000-0000-0000-999999999999"
            },
        )
        for indice, cambios in enumerate(casos, start=1):
            with self.subTest(cambios=cambios):
                with self.assertRaises(IntegrityError):
                    self.repository.guardar(
                        self._control(
                            id_control=(
                                "00000000-0000-0000-0000-"
                                f"{500 + indice:012d}"
                            ),
                            **cambios,
                        )
                    )

    def test_historial_y_ultimo_usan_secuencia(self) -> None:
        primero = self._control(
            fecha_control=datetime(2026, 8, 11, 10)
        )
        segundo = self._control(
            id_control=CONTROL_B_ID,
            fecha_control=datetime(2026, 8, 11, 9),
        )
        self.repository.guardar(primero)
        self.repository.guardar(segundo)

        historial = self.repository.listar_por_documento("DOC-000001")
        ultimo = self.repository.obtener_ultimo_por_documento(
            "DOC-000001"
        )

        self.assertEqual(
            [item.id_control for item in historial],
            [CONTROL_A_ID, CONTROL_B_ID],
        )
        self.assertEqual(ultimo.id_control, CONTROL_B_ID)

    def test_rollback_ante_fallo(self) -> None:
        control = self._control()
        self.repository.guardar(control)

        with self.assertRaises(IntegrityError):
            self.repository.guardar(control)

        self.assertEqual(
            self.repository.listar_por_documento("DOC-000001"),
            [control],
        )

    def _reemplazar_seleccion(self) -> None:
        with self.session_factory() as session:
            seleccion = session.get(
                SeleccionProveedorModel, SELECCION_A_ID
            )
            seleccion.vigente = False
            session.add(self._seleccion_b())
            session.commit()

    def _crear_dependencias(self) -> None:
        with self.session_factory() as session:
            session.add(
                SolicitudIntervencionModel(
                    id_solicitud=SOLICITUD_ID,
                    numero_solicitud="SOL-2026-000001",
                    procedencia="SUNA",
                    id_suna="SUNA-1",
                    fecha_ingreso=date(2026, 8, 10),
                    establecimiento="EP N.º 1",
                    solicitante="Secretaría Técnica",
                    motivo="Intervención",
                    prioridad="ALTA",
                    estado="REGISTRADA",
                )
            )
            session.add(
                DecisionAdministrativaModel(
                    id_decision=DECISION_ID,
                    solicitud_intervencion_id=SOLICITUD_ID,
                    autoridad_decisora="Tesorero",
                    fecha_decision=date(2026, 8, 10),
                    resultado="Aprobar intervención",
                    fundamento="Fundamento",
                    fondo_interviniente="FONDO_COMPENSADOR",
                    descripcion_fondo=None,
                    usuario_registrante="Secretaría Técnica",
                )
            )
            session.add_all(
                [
                    ProveedorModel(
                        id_proveedor=PROVEEDOR_A_ID,
                        cuit="30718078063",
                        razon_social="Proveedor A",
                        activo=True,
                    ),
                    ProveedorModel(
                        id_proveedor=PROVEEDOR_B_ID,
                        cuit="30000000007",
                        razon_social="Proveedor B",
                        activo=True,
                    ),
                ]
            )
            session.add(
                ExpedienteModel(
                    id=EXPEDIENTE_ID,
                    numero_interno="033-1/2026",
                    numero_gdeba=None,
                    solicitud_intervencion_id=SOLICITUD_ID,
                    decision_administrativa_id=DECISION_ID,
                    configuracion_uc_id=None,
                    id_suna=None,
                    tipo_tramite="FONDO_COMPENSADOR",
                    estado="BORRADOR",
                    establecimiento=None,
                    objeto=None,
                    numero_disposicion=None,
                    creado=datetime(2026, 8, 11, 8),
                )
            )
            session.flush()
            session.add(
                DocumentoModel(
                    secuencia=1,
                    expediente_id=EXPEDIENTE_ID,
                    tipo="OP",
                    nombre_archivo="op.pdf",
                    ruta="storage/op.pdf",
                    fecha_carga=datetime(2026, 8, 11, 9),
                    observaciones=None,
                    tamano_bytes=100,
                    mime_type="application/pdf",
                )
            )
            session.add(
                SeleccionProveedorModel(
                    id_seleccion=SELECCION_A_ID,
                    solicitud_intervencion_id=SOLICITUD_ID,
                    decision_administrativa_id=DECISION_ID,
                    proveedor_id=PROVEEDOR_A_ID,
                    fecha_seleccion=datetime(2026, 8, 11, 9),
                    seleccionado_por="Secretaría Técnica",
                    proveedor_cuit="30718078063",
                    proveedor_razon_social="Proveedor A",
                    motivo_reemplazo=None,
                    vigente=True,
                )
            )
            session.commit()

    @staticmethod
    def _seleccion_b() -> SeleccionProveedorModel:
        return SeleccionProveedorModel(
            id_seleccion=SELECCION_B_ID,
            solicitud_intervencion_id=SOLICITUD_ID,
            decision_administrativa_id=DECISION_ID,
            proveedor_id=PROVEEDOR_B_ID,
            fecha_seleccion=datetime(2026, 8, 11, 10),
            seleccionado_por="Secretaría Técnica",
            proveedor_cuit="30000000007",
            proveedor_razon_social="Proveedor B",
            motivo_reemplazo="Reemplazo",
            vigente=True,
        )

    @staticmethod
    def _control(**cambios) -> ControlProveedorOPEvidencia:
        valores = {
            "id_control": CONTROL_A_ID,
            "expediente_id": EXPEDIENTE_ID,
            "documento_op_id": "DOC-000001",
            "solicitud_intervencion_id": SOLICITUD_ID,
            "seleccion_proveedor_id": SELECCION_A_ID,
            "estado": EstadoControlProveedorOP.COINCIDE,
            "proveedor_cuit_seleccionado": "30718078063",
            "proveedor_razon_social_seleccionada": "Proveedor A",
            "cuit_detectado": "30718078063",
            "razon_social_detectada": "Proveedor A",
            "advertencias": (),
            "fecha_control": datetime(2026, 8, 11, 11),
            "modo_analisis": "ALFA_PDF_TEXTO",
        }
        valores.update(cambios)
        return ControlProveedorOPEvidencia(**valores)
