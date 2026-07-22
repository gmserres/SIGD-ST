import unittest
from datetime import date
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.api.decisiones import crear_expediente_desde_decision
from app.schemas.decision_administrativa import DecisionAdministrativaCreate
from app.schemas.decision_expediente import CrearExpedienteDesdeDecision
from app.services.decision_administrativa_service import (
    DecisionAdministrativaService,
)


class FondoIntervinienteTest(unittest.TestCase):
    def test_conserva_fondo_autoridad_y_usuario_registrante(self) -> None:
        service = DecisionAdministrativaService()
        decision = service.crear(
            DecisionAdministrativaCreate(
                solicitud_intervencion_id="solicitud-1",
                autoridad_decisora="Tesorero",
                fecha_decision=date(2026, 7, 22),
                resultado="Aprobar intervención",
                fundamento="Intervención aprobada.",
                fondo_interviniente="FONDO_COMPENSADOR",
                usuario_registrante="Secretario Técnico",
            )
        )

        self.assertEqual(decision.fondo_interviniente, "FONDO_COMPENSADOR")
        self.assertEqual(decision.autoridad_decisora, "Tesorero")
        self.assertEqual(decision.usuario_registrante, "Secretario Técnico")

    def test_rechaza_otro_sin_descripcion(self) -> None:
        with self.assertRaises(ValidationError):
            DecisionAdministrativaCreate(
                solicitud_intervencion_id="solicitud-1",
                autoridad_decisora="Tesorero",
                fecha_decision=date(2026, 7, 22),
                resultado="Aprobar intervención",
                fundamento="Intervención aprobada.",
                fondo_interviniente="OTRO",
                usuario_registrante="Secretario Técnico",
            )

    def test_acepta_y_conserva_otro_con_descripcion(self) -> None:
        service = DecisionAdministrativaService()
        decision = service.crear(
            DecisionAdministrativaCreate(
                solicitud_intervencion_id="solicitud-1",
                autoridad_decisora="Tesorero",
                fecha_decision=date(2026, 7, 22),
                resultado="Aprobar intervención",
                fundamento="Intervención aprobada.",
                fondo_interviniente="OTRO",
                descripcion_fondo="Programa específico",
                usuario_registrante="Secretario Técnico",
            )
        )

        self.assertEqual(decision.fondo_interviniente, "OTRO")
        self.assertEqual(decision.descripcion_fondo, "Programa específico")

    def test_fondo_compensador_habilita_creacion_de_expediente(self) -> None:
        decision = self._crear_decision("Aprobar intervención", "FONDO_COMPENSADOR")
        data = CrearExpedienteDesdeDecision(
            numero_interno="033-115/2026",
            numero_gdeba=None,
        )

        with (
            patch(
                "app.api.decisiones.decision_administrativa_service.obtener_por_id",
                return_value=decision,
            ),
            patch(
                "app.api.decisiones.solicitud_intervencion_service.obtener_por_id"
            ) as obtener_solicitud,
            patch("app.api.decisiones.expediente_service.crear") as crear_expediente,
        ):
            solicitud = obtener_solicitud.return_value
            solicitud.id_solicitud = "solicitud-1"
            solicitud.id_suna = "12345"
            solicitud.establecimiento = "EP 1"
            solicitud.motivo = "Reparación"
            crear_expediente.return_value = "expediente-creado"

            resultado = crear_expediente_desde_decision("decision-1", data)

        self.assertEqual(resultado, "expediente-creado")
        expediente_data = crear_expediente.call_args.args[0]
        self.assertNotIn("fondo_interviniente", type(expediente_data).model_fields)

    def test_rechaza_decision_no_aprobatoria(self) -> None:
        self._assert_conflict(
            self._crear_decision("Rechazar intervención", "FONDO_COMPENSADOR"),
            "La decisión no aprueba la intervención.",
        )

    def test_rechaza_fondo_no_determinado(self) -> None:
        self._assert_conflict(
            self._crear_decision("Aprobar intervención", None),
            "La decisión no tiene un Fondo Interviniente determinado.",
        )

    def test_rechaza_cufp(self) -> None:
        self._assert_conflict(
            self._crear_decision("Aprobar intervención", "CUFP"),
            "El circuito del Fondo Interviniente seleccionado todavía no está implementado.",
        )

    def test_rechaza_otro(self) -> None:
        self._assert_conflict(
            self._crear_decision("Aprobar intervención", "OTRO", "Programa específico"),
            "El circuito del Fondo Interviniente seleccionado todavía no está implementado.",
        )

    @staticmethod
    def _crear_decision(
        resultado: str,
        fondo_interviniente: str | None,
        descripcion_fondo: str | None = None,
    ):
        service = DecisionAdministrativaService()
        return service.crear(
            DecisionAdministrativaCreate(
                solicitud_intervencion_id="solicitud-1",
                autoridad_decisora="Tesorero",
                fecha_decision=date(2026, 7, 22),
                resultado=resultado,
                fundamento="Fundamento",
                fondo_interviniente=fondo_interviniente,
                descripcion_fondo=descripcion_fondo,
                usuario_registrante="Secretario Técnico",
            )
        )

    def _assert_conflict(self, decision, mensaje: str) -> None:
        data = CrearExpedienteDesdeDecision(
            numero_interno="033-115/2026",
            numero_gdeba=None,
        )
        with patch(
            "app.api.decisiones.decision_administrativa_service.obtener_por_id",
            return_value=decision,
        ):
            with self.assertRaises(HTTPException) as contexto:
                crear_expediente_desde_decision("decision-1", data)

        self.assertEqual(contexto.exception.status_code, 409)
        self.assertEqual(contexto.exception.detail, mensaje)


if __name__ == "__main__":
    unittest.main()
