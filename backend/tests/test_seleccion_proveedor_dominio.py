import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

from app.domain.seleccion_proveedor import SeleccionProveedor


class SeleccionProveedorDominioTest(unittest.TestCase):
    def test_crea_seleccion_valida_y_normaliza_snapshot(self):
        seleccion = self._crear(
            proveedor_cuit="30-71807806-3",
            proveedor_razon_social="  Constructora del Sur S.R.L.  ",
            seleccionado_por="  Secretaría Técnica  ",
        )
        self.assertEqual(seleccion.proveedor_cuit, "30718078063")
        self.assertEqual(seleccion.proveedor_razon_social, "Constructora del Sur S.R.L.")
        self.assertEqual(seleccion.seleccionado_por, "Secretaría Técnica")
        self.assertTrue(seleccion.vigente)
        self.assertIsNone(seleccion.motivo_reemplazo)

    def test_rechaza_identificadores_obligatorios_ausentes(self):
        for campo in (
            "id_seleccion",
            "solicitud_intervencion_id",
            "decision_administrativa_id",
            "proveedor_id",
        ):
            with self.subTest(campo=campo):
                with self.assertRaisesRegex(ValueError, f"{campo} es obligatorio."):
                    self._crear(**{campo: "   "})

    def test_rechaza_seleccionado_por_ausente(self):
        with self.assertRaisesRegex(ValueError, "seleccionado_por es obligatorio."):
            self._crear(seleccionado_por="   ")

    def test_rechaza_fecha_seleccion_no_datetime(self):
        with self.assertRaisesRegex(TypeError, "fecha_seleccion debe ser datetime."):
            self._crear(fecha_seleccion="2026-08-10")

    def test_rechaza_vigente_no_booleano(self):
        with self.assertRaisesRegex(TypeError, "vigente debe ser booleano."):
            self._crear(vigente=1)

    def test_rechaza_snapshot_de_cuit_invalido(self):
        with self.assertRaises(ValueError):
            self._crear(proveedor_cuit="30-123")

    def test_normaliza_y_exige_motivo_de_reemplazo(self):
        seleccion = self._crear(
            motivo_reemplazo="  Imposibilidad de cumplimiento  "
        )
        self.assertEqual(
            seleccion.motivo_reemplazo,
            "Imposibilidad de cumplimiento",
        )
        with self.assertRaisesRegex(ValueError, "motivo_reemplazo no puede estar vacío."):
            self._crear(motivo_reemplazo="   ")

    def test_es_inmutable_y_finaliza_vigencia_con_nueva_instancia(self):
        seleccion = self._crear()
        finalizada = seleccion.finalizar_vigencia()
        self.assertIsNot(finalizada, seleccion)
        self.assertTrue(seleccion.vigente)
        self.assertFalse(finalizada.vigente)
        self.assertEqual(finalizada.proveedor_id, seleccion.proveedor_id)
        self.assertEqual(finalizada.proveedor_cuit, seleccion.proveedor_cuit)
        self.assertEqual(
            finalizada.proveedor_razon_social,
            seleccion.proveedor_razon_social,
        )
        with self.assertRaises(FrozenInstanceError):
            seleccion.vigente = False

    @staticmethod
    def _crear(
        *,
        id_seleccion="00000000-0000-0000-0000-000000000101",
        expediente_id="EXP-000001",
        solicitud_intervencion_id="00000000-0000-0000-0000-000000000201",
        decision_administrativa_id="00000000-0000-0000-0000-000000000301",
        proveedor_id="00000000-0000-0000-0000-000000000401",
        fecha_seleccion=datetime(2026, 8, 10, 10, 30),
        seleccionado_por="Secretaría Técnica",
        proveedor_cuit="30-71807806-3",
        proveedor_razon_social="Constructora del Sur S.R.L.",
        motivo_reemplazo=None,
        vigente=True,
    ) -> SeleccionProveedor:
        return SeleccionProveedor(
            id_seleccion=id_seleccion,
            expediente_id=expediente_id,
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
