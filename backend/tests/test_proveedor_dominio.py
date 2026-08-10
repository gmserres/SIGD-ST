import unittest
from dataclasses import FrozenInstanceError

from app.domain.proveedor import Proveedor


class ProveedorDominioTest(unittest.TestCase):
    def test_crea_proveedor_activo_con_cuit_normalizado(self):
        proveedor = self._crear(cuit="30-71807806-3")

        self.assertEqual(proveedor.cuit, "30718078063")
        self.assertTrue(proveedor.activo)

    def test_conserva_cuit_normalizado_sin_guiones(self):
        proveedor = self._crear(cuit="30718078063")

        self.assertEqual(proveedor.cuit, "30718078063")

    def test_rechaza_cuit_incompleto(self):
        with self.assertRaisesRegex(
            ValueError,
            "exactamente 11 dígitos",
        ):
            self._crear(cuit="30-71807806")

    def test_rechaza_caracteres_invalidos_en_cuit(self):
        with self.assertRaisesRegex(
            ValueError,
            "exactamente 11 dígitos",
        ):
            self._crear(cuit="30-A1807806-3")

    def test_rechaza_guiones_en_posiciones_invalidas(self):
        with self.assertRaisesRegex(
            ValueError,
            "exactamente 11 dígitos",
        ):
            self._crear(cuit="307-1807806-3")

    def test_rechaza_identificador_vacio(self):
        with self.assertRaisesRegex(
            ValueError,
            "identificador del proveedor es obligatorio",
        ):
            self._crear(id_proveedor=" ")

    def test_rechaza_identificador_no_textual(self):
        with self.assertRaisesRegex(
            TypeError,
            "identificador del proveedor debe ser texto",
        ):
            self._crear(id_proveedor=1)

    def test_rechaza_cuit_no_textual(self):
        with self.assertRaisesRegex(
            TypeError,
            "CUIT debe ser texto",
        ):
            self._crear(cuit=None)

    def test_rechaza_razon_social_vacia(self):
        with self.assertRaisesRegex(
            ValueError,
            "razón social es obligatoria",
        ):
            self._crear(razon_social=" ")

    def test_rechaza_razon_social_no_textual(self):
        with self.assertRaisesRegex(
            TypeError,
            "razón social debe ser texto",
        ):
            self._crear(razon_social=1)

    def test_normaliza_espacios_exteriores_de_razon_social(self):
        proveedor = self._crear(
            razon_social="  Constructora del Sur S.R.L.  "
        )

        self.assertEqual(
            proveedor.razon_social,
            "Constructora del Sur S.R.L.",
        )

    def test_preserva_capitalizacion_de_razon_social(self):
        proveedor = self._crear(
            razon_social="Servicios Educativos del Sud S.A."
        )

        self.assertEqual(
            proveedor.razon_social,
            "Servicios Educativos del Sud S.A.",
        )

    def test_modifica_razon_social_sin_mutar_instancia_original(self):
        original = self._crear(razon_social="Razón Social Anterior")

        modificado = original.modificar_razon_social(
            "  Razón Social Vigente  "
        )

        self.assertEqual(original.razon_social, "Razón Social Anterior")
        self.assertEqual(modificado.razon_social, "Razón Social Vigente")
        self.assertEqual(modificado.id_proveedor, original.id_proveedor)
        self.assertEqual(modificado.cuit, original.cuit)

    def test_rechaza_modificacion_con_razon_social_vacia(self):
        with self.assertRaisesRegex(
            ValueError,
            "razón social es obligatoria",
        ):
            self._crear().modificar_razon_social(" ")

    def test_inactiva_y_activa_sin_modificar_identidad(self):
        original = self._crear()

        inactivo = original.inactivar()
        reactivado = inactivo.activar()

        self.assertFalse(inactivo.activo)
        self.assertTrue(reactivado.activo)
        self.assertEqual(inactivo.id_proveedor, original.id_proveedor)
        self.assertEqual(inactivo.cuit, original.cuit)
        self.assertEqual(inactivo.razon_social, original.razon_social)

    def test_es_inmutable(self):
        with self.assertRaises(FrozenInstanceError):
            self._crear().razon_social = "Otra razón social"

    def test_rechaza_estado_activo_no_booleano(self):
        with self.assertRaisesRegex(
            TypeError,
            "estado activo debe ser booleano",
        ):
            self._crear(activo=1)

    @staticmethod
    def _crear(
        *,
        id_proveedor: str = (
            "00000000-0000-0000-0000-000000000001"
        ),
        cuit: str = "30-71807806-3",
        razon_social: str = "Constructora del Sur S.R.L.",
        activo: bool = True,
    ) -> Proveedor:
        return Proveedor(
            id_proveedor=id_proveedor,
            cuit=cuit,
            razon_social=razon_social,
            activo=activo,
        )
