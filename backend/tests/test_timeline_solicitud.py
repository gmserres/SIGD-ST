from datetime import date, datetime
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

from app.api.solicitudes import listar_timeline_solicitud
from app.repositories.timeline_solicitud_repository import (
    FuentesTimelineSolicitud,
)
from app.schemas.timeline_expediente import EventoTimelineExpedienteRead
from app.services.historial import HistorialService
from app.services.timeline_solicitud import (
    SolicitudTimelineInexistenteError,
    TimelineSolicitudService,
)


def ns(**valores):
    return SimpleNamespace(**valores)


class RepositorioSolicitudFake:
    def __init__(self, fuentes):
        self.fuentes = fuentes

    def obtener_fuentes(self, solicitud_id):
        return self.fuentes.get(solicitud_id)


class TimelineExpedienteFake:
    def __init__(self, eventos):
        self.eventos = eventos
        self.consultados = []

    def obtener(self, expediente_id):
        self.consultados.append(expediente_id)
        return self.eventos.get(expediente_id, [])


class TimelineSolicitudTest(TestCase):
    def _solicitud(self, solicitud_id="SOL-A"):
        return ns(
            id_solicitud=solicitud_id,
            fecha_ingreso=date(2026, 8, 1),
        )

    def _expediente(
        self,
        expediente_id,
        creado,
        estado="VALIDADO",
    ):
        return ns(
            id=expediente_id,
            numero_interno=f"{expediente_id}/2026",
            numero_gdeba=None,
            estado=estado,
            creado=creado,
            secuencia=int(expediente_id[-1]) if expediente_id[-1].isdigit() else 1,
        )

    def _evento(
        self,
        tipo,
        fecha,
        entidad_id,
        documento_op_id=None,
        metadatos=None,
    ):
        return EventoTimelineExpedienteRead(
            tipo=tipo,
            fecha_hora=fecha,
            titulo=tipo.replace("_", " ").title(),
            entidad_origen="EXPEDIENTE",
            entidad_origen_id=entidad_id,
            documento_op_id=documento_op_id,
            metadatos=metadatos or {},
        )

    def _servicio(self, fuentes, eventos=None):
        timeline_expediente = TimelineExpedienteFake(eventos or {})
        servicio = TimelineSolicitudService(
            RepositorioSolicitudFake(
                {fuentes.solicitud.id_solicitud: fuentes}
            ),
            timeline_expediente,
        )
        return servicio, timeline_expediente

    def test_solicitud_sin_expedientes_conserva_historia_propia(self):
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[],
        )
        servicio, timeline_expediente = self._servicio(fuentes)
        eventos = servicio.obtener("SOL-A")
        self.assertEqual([e.tipo for e in eventos], ["SOLICITUD_INGRESADA"])
        self.assertIsNone(eventos[0].expediente_id)
        self.assertEqual(timeline_expediente.consultados, [])

    def test_decision_es_actuacion_de_solicitud(self):
        decision = ns(
            id_decision="DEC-1",
            fecha_decision=date(2026, 8, 2),
            resultado="Aprobar intervención",
            autoridad_decisora="Autoridad",
            fundamento="Fundamento durable",
            fondo_interviniente="FONDO_COMPENSADOR",
            descripcion_fondo=None,
            usuario_registrante="secretaria",
        )
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[decision],
            expedientes=[],
        )
        eventos = self._servicio(fuentes)[0].obtener("SOL-A")
        evento = next(e for e in eventos if e.tipo == "DECISION_ADMINISTRATIVA")
        self.assertEqual(evento.nivel, "SOLICITUD")
        self.assertIsNone(evento.expediente_id)
        self.assertEqual(evento.precision_temporal, "DIA")

    def test_un_expediente_reutiliza_e2b_sin_duplicar_creacion(self):
        expediente = self._expediente(
            "EXP-1", datetime(2026, 8, 2, 10)
        )
        creacion = self._evento(
            "EXPEDIENTE_CREADO",
            expediente.creado,
            expediente.id,
        )
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[expediente],
        )
        servicio, timeline_e2b = self._servicio(
            fuentes,
            {"EXP-1": [creacion]},
        )
        eventos = servicio.obtener("SOL-A")
        self.assertEqual(
            sum(e.tipo == "EXPEDIENTE_CREADO" for e in eventos), 1
        )
        agregado = next(e for e in eventos if e.tipo == "EXPEDIENTE_CREADO")
        self.assertEqual(agregado.nivel, "EXPEDIENTE")
        self.assertEqual(agregado.expediente_id, "EXP-1")
        self.assertEqual(timeline_e2b.consultados, ["EXP-1"])

    def test_varios_expedientes_preservan_identidad_y_orden_global(self):
        exp_a = self._expediente("EXP-1", datetime(2026, 8, 2, 10))
        exp_b = self._expediente("EXP-2", datetime(2026, 8, 2, 11))
        eventos_e2b = {
            "EXP-1": [
                self._evento(
                    "OP_INCORPORADA",
                    datetime(2026, 8, 2, 12),
                    "DOC-1",
                    "DOC-000001",
                )
            ],
            "EXP-2": [
                self._evento(
                    "PROVEEDOR_SELECCIONADO",
                    datetime(2026, 8, 2, 11, 30),
                    "SEL-2",
                )
            ],
        }
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[exp_a, exp_b],
        )
        eventos = self._servicio(fuentes, eventos_e2b)[0].obtener("SOL-A")
        ramas = [e for e in eventos if e.nivel == "EXPEDIENTE"]
        self.assertEqual(eventos[0].tipo, "SOLICITUD_INGRESADA")
        self.assertEqual(
            [e.expediente_id for e in ramas], ["EXP-2", "EXP-1"]
        )
        self.assertEqual(ramas[1].documento_op_id, "DOC-000001")

    def test_varias_op_controles_disposiciones_y_formalizaciones(self):
        expediente = self._expediente("EXP-1", datetime(2026, 8, 2, 10))
        tipos = [
            "OP_INCORPORADA",
            "CONTROL_PROVEEDOR_OP",
            "DISPOSICION_EMITIDA",
            "DISPOSICION_FORMALIZADA",
        ]
        eventos_e2b = {
            "EXP-1": [
                self._evento(
                    tipo,
                    datetime(2026, 8, 3, indice),
                    f"ORIGEN-{indice}",
                    f"DOC-{op:06d}",
                )
                for op in (1, 2)
                for indice, tipo in enumerate(tipos, start=9 + op * 4)
            ]
        }
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[expediente],
        )
        eventos = self._servicio(fuentes, eventos_e2b)[0].obtener("SOL-A")
        ramas = [e for e in eventos if e.nivel == "EXPEDIENTE"]
        self.assertEqual(
            {e.documento_op_id for e in ramas},
            {"DOC-000001", "DOC-000002"},
        )
        self.assertEqual(
            sum(e.tipo == "DISPOSICION_FORMALIZADA" for e in ramas), 2
        )

    def test_finalizacion_de_expediente_no_finaliza_solicitud(self):
        expediente = self._expediente(
            "EXP-1", datetime(2026, 8, 2, 10), "DESISTIDO"
        )
        eventos_e2b = {
            "EXP-1": [
                self._evento(
                    "PROVEEDOR_SELECCIONADO",
                    datetime(2026, 8, 2, 11),
                    "SEL-1",
                ),
                self._evento(
                    "EXPEDIENTE_DESISTIDO",
                    datetime(2026, 8, 3, 11),
                    "EXP-1",
                ),
                self._evento(
                    "EXPEDIENTE_ARCHIVADO",
                    datetime(2026, 8, 4),
                    "EXP-1",
                    metadatos={"precision_fecha": "DIA"},
                ),
            ]
        }
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[expediente],
        )
        eventos = self._servicio(fuentes, eventos_e2b)[0].obtener("SOL-A")
        finalizaciones = [
            e
            for e in eventos
            if e.tipo in {"EXPEDIENTE_DESISTIDO", "EXPEDIENTE_ARCHIVADO"}
        ]
        self.assertTrue(all(e.nivel == "EXPEDIENTE" for e in finalizaciones))
        self.assertTrue(all(e.expediente_id == "EXP-1" for e in finalizaciones))

    def test_reinicio_historial_no_modifica_timeline(self):
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[],
        )
        servicio = self._servicio(fuentes)[0]
        historial = HistorialService()
        historial.registrar("EXP-1", "EVENTO_EFIMERO")
        antes = servicio.obtener("SOL-A")
        historial = HistorialService()
        self.assertEqual(historial.listar_por_expediente("EXP-1"), [])
        despues = servicio.obtener("SOL-A")
        self.assertEqual(antes, despues)

    def test_solicitudes_distintas_no_se_contaminan(self):
        fuentes_a = FuentesTimelineSolicitud(
            solicitud=self._solicitud("SOL-A"),
            decisiones=[],
            expedientes=[
                self._expediente("EXP-1", datetime(2026, 8, 2, 10))
            ],
        )
        fuentes_b = FuentesTimelineSolicitud(
            solicitud=self._solicitud("SOL-B"),
            decisiones=[],
            expedientes=[
                self._expediente("EXP-2", datetime(2026, 8, 2, 11))
            ],
        )
        repo = RepositorioSolicitudFake(
            {"SOL-A": fuentes_a, "SOL-B": fuentes_b}
        )
        timeline_e2b = TimelineExpedienteFake(
            {
                "EXP-1": [
                    self._evento(
                        "OP_INCORPORADA",
                        datetime(2026, 8, 3, 10),
                        "DOC-A",
                        "DOC-000001",
                    )
                ],
                "EXP-2": [
                    self._evento(
                        "OP_INCORPORADA",
                        datetime(2026, 8, 3, 11),
                        "DOC-B",
                        "DOC-000002",
                    )
                ],
            }
        )
        servicio = TimelineSolicitudService(repo, timeline_e2b)
        eventos_a = servicio.obtener("SOL-A")
        self.assertNotIn("EXP-2", {e.expediente_id for e in eventos_a})
        self.assertNotIn("DOC-000002", {e.documento_op_id for e in eventos_a})

    def test_determinismo_en_empates(self):
        expediente = self._expediente("EXP-1", datetime(2026, 8, 2, 10))
        eventos_e2b = {
            "EXP-1": [
                self._evento(
                    "OP_INCORPORADA",
                    datetime(2026, 8, 3, 10),
                    "DOC-B",
                    "DOC-000002",
                ),
                self._evento(
                    "OP_INCORPORADA",
                    datetime(2026, 8, 3, 10),
                    "DOC-A",
                    "DOC-000001",
                ),
            ]
        }
        fuentes = FuentesTimelineSolicitud(
            solicitud=self._solicitud(),
            decisiones=[],
            expedientes=[expediente],
        )
        servicio = self._servicio(fuentes, eventos_e2b)[0]
        primero = servicio.obtener("SOL-A")
        segundo = servicio.obtener("SOL-A")
        self.assertEqual(primero, segundo)
        ops = [e.entidad_origen_id for e in primero if e.tipo == "OP_INCORPORADA"]
        self.assertEqual(ops, ["DOC-A", "DOC-B"])

    def test_endpoint_404_y_sin_historial_service(self):
        with patch(
            "app.api.solicitudes.timeline_solicitud_service.obtener",
            side_effect=SolicitudTimelineInexistenteError("SOL-X"),
        ), patch(
            "app.services.historial.historial_service."
            "listar_por_expediente",
            side_effect=AssertionError("No debe consultar historial"),
        ):
            with self.assertRaises(HTTPException) as contexto:
                listar_timeline_solicitud("SOL-X")
        self.assertEqual(contexto.exception.status_code, 404)
