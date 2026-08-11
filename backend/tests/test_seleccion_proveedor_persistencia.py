import unittest
from datetime import date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.domain.seleccion_proveedor import SeleccionProveedor
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.seleccion_proveedor_mapper import a_dominio, a_modelo
from app.infrastructure.database.models.decision_administrativa_model import DecisionAdministrativaModel
from app.infrastructure.database.models.proveedor_model import ProveedorModel
from app.infrastructure.database.models.solicitud_intervencion_model import SolicitudIntervencionModel
from app.infrastructure.database.repositories.seleccion_proveedor_postgres_repository import PostgresSeleccionProveedorRepository


SOLICITUD_ID = "00000000-0000-0000-0000-000000000201"
DECISION_ID = "00000000-0000-0000-0000-000000000301"
PROVEEDOR_ID = "00000000-0000-0000-0000-000000000401"
PROVEEDOR_NUEVO_ID = "00000000-0000-0000-0000-000000000402"
SELECCION_ID = "00000000-0000-0000-0000-000000000101"
SELECCION_NUEVA_ID = "00000000-0000-0000-0000-000000000102"


class SeleccionProveedorPersistenciaTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")

        @event.listens_for(self.engine, "connect")
        def habilitar_claves_foraneas(conexion, _registro):
            cursor = conexion.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.repository = PostgresSeleccionProveedorRepository(self.session_factory)
        self._crear_dependencias()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_mapper_ida_y_vuelta_conserva_todos_los_campos(self):
        seleccion = self._crear_seleccion()
        self.assertEqual(a_dominio(a_modelo(seleccion)), seleccion)

    def test_guarda_y_recupera_seleccion_vigente(self):
        seleccion = self._crear_seleccion()
        self.repository.guardar(seleccion)
        self.assertEqual(self.repository.obtener_por_id(seleccion.id_seleccion), seleccion)
        self.assertEqual(self.repository.obtener_vigente_por_solicitud(SOLICITUD_ID), seleccion)

    def test_impide_dos_selecciones_vigentes_para_solicitud(self):
        primera = self._crear_seleccion()
        segunda = self._crear_seleccion(
            id_seleccion=SELECCION_NUEVA_ID,
            proveedor_id=PROVEEDOR_NUEVO_ID,
            proveedor_cuit="30-00000000-7",
            proveedor_razon_social="Proveedor Nuevo",
        )
        self.repository.guardar(primera)
        with self.assertRaises(IntegrityError):
            self.repository.guardar(segunda)
        self.assertEqual(self.repository.obtener_vigente_por_solicitud(SOLICITUD_ID), primera)

    def test_reemplazo_preserva_anterior_y_deja_una_vigente(self):
        anterior = self._crear_seleccion()
        nueva = self._crear_nueva()
        self.repository.guardar(anterior)
        self.repository.reemplazar(anterior, nueva)
        anterior_persistida = self.repository.obtener_por_id(anterior.id_seleccion)
        historial = self.repository.listar_por_solicitud(SOLICITUD_ID)
        self.assertFalse(anterior_persistida.vigente)
        self.assertEqual(self.repository.obtener_vigente_por_solicitud(SOLICITUD_ID), nueva)
        self.assertEqual(len(historial), 2)
        self.assertEqual(sum(item.vigente for item in historial), 1)

    def test_historial_tiene_orden_determinista(self):
        anterior = self._crear_seleccion(fecha_seleccion=datetime(2026, 8, 10, 9))
        nueva = self._crear_nueva(fecha_seleccion=datetime(2026, 8, 11, 9))
        self.repository.guardar(anterior)
        self.repository.reemplazar(anterior, nueva)
        self.assertEqual(
            [item.id_seleccion for item in self.repository.listar_por_solicitud(SOLICITUD_ID)],
            [SELECCION_ID, SELECCION_NUEVA_ID],
        )

    def test_snapshots_no_cambian_al_modificar_maestro(self):
        seleccion = self._crear_seleccion(proveedor_razon_social="Proveedor Original")
        self.repository.guardar(seleccion)
        with self.session_factory() as session:
            proveedor = session.get(ProveedorModel, PROVEEDOR_ID)
            proveedor.razon_social = "Razón Social Modificada"
            proveedor.activo = False
            session.commit()
        recuperada = self.repository.obtener_por_id(seleccion.id_seleccion)
        self.assertEqual(recuperada.proveedor_cuit, "30718078063")
        self.assertEqual(recuperada.proveedor_razon_social, "Proveedor Original")
        self.assertTrue(recuperada.vigente)

    def test_fk_rechaza_solicitud_inexistente(self):
        with self.assertRaises(IntegrityError):
            self.repository.guardar(self._crear_seleccion(
                solicitud_intervencion_id="00000000-0000-0000-0000-999999999999"
            ))

    def test_fk_rechaza_decision_inexistente(self):
        with self.assertRaises(IntegrityError):
            self.repository.guardar(self._crear_seleccion(
                decision_administrativa_id="00000000-0000-0000-0000-999999999999"
            ))

    def test_fk_rechaza_proveedor_inexistente(self):
        with self.assertRaises(IntegrityError):
            self.repository.guardar(self._crear_seleccion(
                proveedor_id="00000000-0000-0000-0000-999999999999"
            ))

    def test_reemplazo_hace_rollback_si_falla_nueva_seleccion(self):
        anterior = self._crear_seleccion()
        nueva_invalida = self._crear_nueva(id_seleccion=anterior.id_seleccion)
        self.repository.guardar(anterior)
        with self.assertRaises(IntegrityError):
            self.repository.reemplazar(anterior, nueva_invalida)
        historial = self.repository.listar_por_solicitud(SOLICITUD_ID)
        self.assertEqual(self.repository.obtener_vigente_por_solicitud(SOLICITUD_ID), anterior)
        self.assertEqual(historial, [anterior])
        self.assertTrue(historial[0].vigente)

    def _crear_dependencias(self):
        with self.session_factory() as session:
            session.add(SolicitudIntervencionModel(
                id_solicitud=SOLICITUD_ID,
                numero_solicitud="SOL-2026-000001",
                procedencia="SUNA",
                id_suna="SUNA-1",
                fecha_ingreso=date(2026, 8, 10),
                establecimiento="EP N.º 1",
                solicitante="Secretaría Técnica",
                motivo="Intervención de prueba",
                prioridad="ALTA",
                estado="REGISTRADA",
            ))
            session.add(DecisionAdministrativaModel(
                id_decision=DECISION_ID,
                solicitud_intervencion_id=SOLICITUD_ID,
                autoridad_decisora="Tesorero",
                fecha_decision=date(2026, 8, 10),
                resultado="Aprobar intervención",
                fundamento="Intervención aprobada.",
                fondo_interviniente="FONDO_COMPENSADOR",
                descripcion_fondo=None,
                usuario_registrante="Secretaría Técnica",
            ))
            session.add_all([
                ProveedorModel(id_proveedor=PROVEEDOR_ID, cuit="30718078063", razon_social="Proveedor Original", activo=True),
                ProveedorModel(id_proveedor=PROVEEDOR_NUEVO_ID, cuit="30000000007", razon_social="Proveedor Nuevo", activo=True),
            ])
            session.commit()

    @staticmethod
    def _crear_seleccion(
        *,
        id_seleccion=SELECCION_ID,
        solicitud_intervencion_id=SOLICITUD_ID,
        decision_administrativa_id=DECISION_ID,
        proveedor_id=PROVEEDOR_ID,
        fecha_seleccion=datetime(2026, 8, 10, 10, 30),
        seleccionado_por="Secretaría Técnica",
        proveedor_cuit="30-71807806-3",
        proveedor_razon_social="Proveedor Original",
        motivo_reemplazo=None,
        vigente=True,
    ):
        return SeleccionProveedor(
            id_seleccion=id_seleccion,
            solicitud_intervencion_id=solicitud_intervencion_id,
            decision_administrativa_id=decision_administrativa_id,
            proveedor_id=proveedor_id,
            fecha_seleccion=fecha_seleccion,
            seleccionado_por=seleccionado_por,
            proveedor_cuit=proveedor_cuit,
            proveedor_razon_social=proveedor_razon_social,
            motivo_reemplazo=motivo_reemplazo,
            vigente=vigente,
        )

    @classmethod
    def _crear_nueva(cls, **cambios):
        valores = dict(
            id_seleccion=SELECCION_NUEVA_ID,
            proveedor_id=PROVEEDOR_NUEVO_ID,
            proveedor_cuit="30-00000000-7",
            proveedor_razon_social="Proveedor Nuevo",
            motivo_reemplazo="Imposibilidad de cumplimiento",
            fecha_seleccion=datetime(2026, 8, 11, 9),
        )
        valores.update(cambios)
        return cls._crear_seleccion(**valores)
