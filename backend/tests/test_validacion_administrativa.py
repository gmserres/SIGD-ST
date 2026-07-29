from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

from app.api.expedientes import generar_borrador_disposicion
from app.domain.estados import EstadoExpediente
from app.schemas.checklist_fisico import ChecklistFisicoRead
from app.schemas.expediente import ExpedienteRead
from app.services.checklist_fisico import checklist_fisico_service
from app.composition.documento import documento_service
from app.composition.expediente import expediente_service
from app.services.validaciones import ValidacionService


class ValidacionAdministrativaTest(TestCase):
    def setUp(self) -> None:
        self.expediente = ExpedienteRead(
            id="EXP-PRUEBA",
            numero_interno="033-115/2026",
            numero_gdeba=None,
            solicitud_intervencion_id="solicitud-prueba",
            decision_administrativa_id="decision-prueba",
            id_suna="1405569",
            tipo_tramite="FONDO_COMPENSADOR",
            estado=EstadoExpediente.BORRADOR,
            establecimiento="EP N° 13",
            objeto="Reparación de cocina industrial",
            numero_disposicion=None,
            creado=datetime(2026, 7, 22, 10, 0),
        )
        self.checklist = ChecklistFisicoRead(
            expediente_id=self.expediente.id,
            factura=True,
            remito_conformidad=True,
            cae=True,
            arca=True,
            arba=True,
            observaciones=None,
            usuario="Secretario Técnico",
            fecha=datetime(2026, 7, 22, 10, 30),
        )

    def test_permite_validar_sin_numero_disposicion_y_sin_op(
        self,
    ) -> None:
        servicio = ValidacionService()

        with (
            patch.object(
                expediente_service,
                "obtener",
                return_value=self.expediente,
            ),
            patch.object(
                documento_service,
                "listar_por_expediente",
                return_value=[],
            ),
            patch.object(
                checklist_fisico_service,
                "obtener",
                return_value=self.checklist,
            ),
        ):
            resultado = servicio.validar(
                self.expediente.id,
                registrar_historial=False,
            )

        self.assertEqual(resultado.estado_general, "VERDE")
        self.assertEqual(resultado.errores, [])
        self.assertEqual(resultado.advertencias, [])
        self.assertNotIn(
            "Número de disposición",
            [control.control for control in resultado.controles],
        )

    def test_mantiene_los_demas_requisitos_bloqueantes(
        self,
    ) -> None:
        servicio = ValidacionService()
        expediente_sin_numero_interno = self.expediente.model_copy(
            update={"numero_interno": ""}
        )

        with (
            patch.object(
                expediente_service,
                "obtener",
                return_value=expediente_sin_numero_interno,
            ),
            patch.object(
                documento_service,
                "listar_por_expediente",
                return_value=[],
            ),
            patch.object(
                checklist_fisico_service,
                "obtener",
                return_value=self.checklist,
            ),
        ):
            resultado = servicio.validar(
                expediente_sin_numero_interno.id,
                registrar_historial=False,
            )

        self.assertEqual(resultado.estado_general, "ROJO")
        self.assertIn(
            "Falta número de expediente interno.",
            resultado.errores,
        )

    def test_disposicion_continua_bloqueada_sin_validacion(
        self,
    ) -> None:
        with (
            patch(
                "app.api.expedientes.obtener_expediente",
                return_value=self.expediente,
            ),
            patch(
                "app.api.expedientes._verificar_op_legible_para_disposicion"
            ) as verificar_op,
        ):
            with self.assertRaises(HTTPException) as contexto:
                generar_borrador_disposicion(self.expediente.id)

        self.assertEqual(contexto.exception.status_code, 409)
        verificar_op.assert_not_called()
