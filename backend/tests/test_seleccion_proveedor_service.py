import unittest
from datetime import date, datetime
from unittest.mock import patch

from pydantic import ValidationError

from app.domain.decision_administrativa import DecisionAdministrativa
from app.domain.proveedor import Proveedor
from app.domain.seleccion_proveedor import (
    DecisionNoAprobatoriaError,
    DecisionSeleccionInexistenteError,
    DecisionSolicitudInconsistenteError,
    MismoProveedorSeleccionadoError,
    ProveedorInactivoError,
    ProveedorSeleccionInexistenteError,
    SeleccionProveedorVigenteError,
    SolicitudSeleccionInexistenteError,
)
from app.domain.solicitud_intervencion import SolicitudIntervencion
from app.schemas.seleccion_proveedor import ReemplazoProveedorCreate, SeleccionProveedorCreate
from app.services.seleccion_proveedor_service import SeleccionProveedorService


SOLICITUD_ID = "00000000-0000-0000-0000-000000000201"
OTRA_SOLICITUD_ID = "00000000-0000-0000-0000-000000000202"
DECISION_ID = "00000000-0000-0000-0000-000000000301"
DECISION_ANTERIOR_ID = "00000000-0000-0000-0000-000000000300"
DECISION_POSTERIOR_ID = "00000000-0000-0000-0000-000000000302"
PROVEEDOR_ID = "00000000-0000-0000-0000-000000000401"
PROVEEDOR_NUEVO_ID = "00000000-0000-0000-0000-000000000402"


class SolicitudRepositoryFake:
    def __init__(self):
        self.solicitudes = {SOLICITUD_ID: SolicitudIntervencion(
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
        )}

    def obtener_por_id(self, solicitud_id):
        return self.solicitudes.get(solicitud_id)


class DecisionRepositoryFake:
    def __init__(self):
        self.decisiones = []

    def listar(self, *, solicitud_intervencion_id=None):
        return list(self.decisiones)


class ProveedorRepositoryFake:
    def __init__(self):
        self.proveedores = {
            PROVEEDOR_ID: Proveedor(PROVEEDOR_ID, "30-71807806-3", "Proveedor Original", True),
            PROVEEDOR_NUEVO_ID: Proveedor(PROVEEDOR_NUEVO_ID, "30-00000000-7", "Proveedor Nuevo", True),
        }

    def obtener_por_id(self, proveedor_id):
        return self.proveedores.get(proveedor_id)


class SeleccionRepositoryFake:
    def __init__(self):
        self.selecciones = []

    def guardar(self, seleccion):
        self.selecciones.append(seleccion)

    def reemplazar(self, anterior, nueva):
        self.selecciones = [
            item.finalizar_vigencia() if item.id_seleccion == anterior.id_seleccion else item
            for item in self.selecciones
        ]
        self.selecciones.append(nueva)

    def obtener_vigente_por_solicitud(self, solicitud_id):
        return next((item for item in self.selecciones if item.solicitud_intervencion_id == solicitud_id and item.vigente), None)

    def listar_por_solicitud(self, solicitud_id):
        return sorted(
            (item for item in self.selecciones if item.solicitud_intervencion_id == solicitud_id),
            key=lambda item: (item.fecha_seleccion, item.id_seleccion),
        )


class SeleccionProveedorServiceTest(unittest.TestCase):
    def setUp(self):
        self.solicitudes = SolicitudRepositoryFake()
        self.decisiones = DecisionRepositoryFake()
        self.proveedores = ProveedorRepositoryFake()
        self.selecciones = SeleccionRepositoryFake()
        self.service = SeleccionProveedorService(
            self.solicitudes,
            self.decisiones,
            self.proveedores,
            self.selecciones,
        )

    def test_selecciona_con_unica_decision_aprobatoria(self):
        self.decisiones.decisiones = [self._decision(DECISION_ID, "Aprobar intervención")]
        seleccion = self.service.seleccionar(SOLICITUD_ID, self._data())
        self.assertEqual(seleccion.decision_administrativa_id, DECISION_ID)
        self.assertEqual(seleccion.solicitud_intervencion_id, SOLICITUD_ID)
        self.assertTrue(seleccion.vigente)

    def test_selecciona_con_aprobacion_posterior_a_decision_no_aprobatoria(self):
        self.decisiones.decisiones = [
            self._decision(DECISION_ANTERIOR_ID, "Solicitar información adicional", fecha=date(2026, 8, 9)),
            self._decision(DECISION_POSTERIOR_ID, "Aprobar intervención", fecha=date(2026, 8, 10)),
        ]
        seleccion = self.service.seleccionar(SOLICITUD_ID, self._data())
        self.assertEqual(seleccion.decision_administrativa_id, DECISION_POSTERIOR_ID)

    def test_impide_seleccion_si_la_ultima_decision_no_es_aprobatoria(self):
        self.decisiones.decisiones = [
            self._decision(DECISION_ANTERIOR_ID, "Aprobar intervención", fecha=date(2026, 8, 9)),
            self._decision(DECISION_POSTERIOR_ID, "Rechazar intervención", fecha=date(2026, 8, 10)),
        ]
        with self.assertRaisesRegex(DecisionNoAprobatoriaError, "La última Decisión no aprueba la intervención."):
            self.service.seleccionar(SOLICITUD_ID, self._data())
        self.assertEqual(self.selecciones.selecciones, [])

    def test_impide_seleccion_para_solicitud_inexistente(self):
        with self.assertRaises(SolicitudSeleccionInexistenteError):
            self.service.seleccionar(OTRA_SOLICITUD_ID, self._data())

    def test_impide_seleccion_sin_decision(self):
        with self.assertRaises(DecisionSeleccionInexistenteError):
            self.service.seleccionar(SOLICITUD_ID, self._data())

    def test_impide_decision_incongruente_con_solicitud(self):
        self.decisiones.decisiones = [self._decision(DECISION_ID, "Aprobar intervención", solicitud=OTRA_SOLICITUD_ID)]
        with self.assertRaises(DecisionSolicitudInconsistenteError):
            self.service.seleccionar(SOLICITUD_ID, self._data())

    def test_impide_seleccion_de_proveedor_inexistente(self):
        self._aprobar()
        with self.assertRaises(ProveedorSeleccionInexistenteError):
            self.service.seleccionar(SOLICITUD_ID, SeleccionProveedorCreate(
                proveedor_id="00000000-0000-0000-0000-999999999999",
                seleccionado_por="Secretaría Técnica",
            ))

    def test_impide_seleccion_de_proveedor_inactivo(self):
        self._aprobar()
        self.proveedores.proveedores[PROVEEDOR_ID] = self.proveedores.proveedores[PROVEEDOR_ID].inactivar()
        with self.assertRaises(ProveedorInactivoError):
            self.service.seleccionar(SOLICITUD_ID, self._data())

    def test_impide_segunda_seleccion_vigente(self):
        self._aprobar()
        self.service.seleccionar(SOLICITUD_ID, self._data())
        with self.assertRaises(SeleccionProveedorVigenteError):
            self.service.seleccionar(SOLICITUD_ID, SeleccionProveedorCreate(
                proveedor_id=PROVEEDOR_NUEVO_ID,
                seleccionado_por="Secretaría Técnica",
            ))
        self.assertEqual(len(self.selecciones.selecciones), 1)

    def test_construye_snapshots_desde_maestro(self):
        self._aprobar()
        seleccion = self.service.seleccionar(SOLICITUD_ID, self._data())
        self.assertEqual(seleccion.proveedor_cuit, "30718078063")
        self.assertEqual(seleccion.proveedor_razon_social, "Proveedor Original")
        self.proveedores.proveedores[PROVEEDOR_ID] = self.proveedores.proveedores[PROVEEDOR_ID].modificar_razon_social("Razón Social Posterior")
        self.assertEqual(self.service.obtener_vigente(SOLICITUD_ID).proveedor_razon_social, "Proveedor Original")

    def test_reemplaza_y_preserva_seleccion_anterior(self):
        self._aprobar()
        instante = datetime(2026, 8, 11, 10, 30)
        with patch(
            "app.services.seleccion_proveedor_service.datetime"
        ) as reloj:
            reloj.now.return_value = instante
            anterior = self.service.seleccionar(
                SOLICITUD_ID,
                self._data(),
            )
            nueva = self.service.reemplazar(
                SOLICITUD_ID,
                ReemplazoProveedorCreate(
                    proveedor_id=PROVEEDOR_NUEVO_ID,
                    seleccionado_por="Secretaría Técnica",
                    motivo_reemplazo=(
                        "Imposibilidad de cumplimiento"
                    ),
                ),
            )

        historial = self.service.listar_historial(SOLICITUD_ID)

        self.assertEqual(len(historial), 2)
        self.assertEqual(historial[0].id_seleccion, anterior.id_seleccion)
        self.assertFalse(historial[0].vigente)
        self.assertEqual(historial[1].id_seleccion, nueva.id_seleccion)
        self.assertTrue(historial[1].vigente)
        self.assertEqual(
            historial[0].fecha_seleccion,
            instante,
        )
        self.assertGreater(
            historial[1].fecha_seleccion,
            historial[0].fecha_seleccion,
        )

    def test_reemplazo_exige_motivo_y_proveedor_diferente(self):
        self._aprobar()
        self.service.seleccionar(SOLICITUD_ID, self._data())
        sin_motivo = ReemplazoProveedorCreate.model_construct(
            proveedor_id=PROVEEDOR_NUEVO_ID,
            seleccionado_por="Secretaría Técnica",
            motivo_reemplazo="   ",
        )
        with self.assertRaises(ValueError):
            self.service.reemplazar(SOLICITUD_ID, sin_motivo)
        with self.assertRaises(MismoProveedorSeleccionadoError):
            self.service.reemplazar(SOLICITUD_ID, ReemplazoProveedorCreate(
                proveedor_id=PROVEEDOR_ID,
                seleccionado_por="Secretaría Técnica",
                motivo_reemplazo="Reasignación",
            ))
        with self.assertRaises(ValidationError):
            ReemplazoProveedorCreate(
                proveedor_id=PROVEEDOR_NUEVO_ID,
                seleccionado_por="Secretaría Técnica",
                motivo_reemplazo="   ",
            )

    def _aprobar(self):
        self.decisiones.decisiones = [self._decision(DECISION_ID, "Aprobar intervención")]

    @staticmethod
    def _data():
        return SeleccionProveedorCreate(
            proveedor_id=PROVEEDOR_ID,
            seleccionado_por="Secretaría Técnica",
        )

    @staticmethod
    def _decision(decision_id, resultado, *, solicitud=SOLICITUD_ID, fecha=date(2026, 8, 10)):
        return DecisionAdministrativa(
            id_decision=decision_id,
            solicitud_intervencion_id=solicitud,
            autoridad_decisora="Tesorero",
            fecha_decision=fecha,
            resultado=resultado,
            fundamento="Fundamento",
            fondo_interviniente="FONDO_COMPENSADOR" if resultado == "Aprobar intervención" else None,
            descripcion_fondo=None,
            usuario_registrante="Secretaría Técnica",
        )
