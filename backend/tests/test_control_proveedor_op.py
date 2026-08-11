import unittest

from app.domain.control_proveedor_op import (
    ADVERTENCIA_RAZON_SOCIAL_DIFERENTE,
    ADVERTENCIA_RAZON_SOCIAL_NO_VERIFICABLE,
    EstadoControlProveedorOP,
    comparar_proveedor_op,
)


class ControlProveedorOPTest(unittest.TestCase):
    def test_cuit_iguales_normalizados_coinciden(self) -> None:
        resultado = self._comparar()

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.COINCIDE,
        )
        self.assertEqual(resultado.cuit_seleccionado, "30718078063")
        self.assertEqual(resultado.cuit_detectado, "30718078063")

    def test_cuit_detectado_con_guiones_coincide(self) -> None:
        resultado = self._comparar(
            cuit_detectado="30-71807806-3"
        )

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.COINCIDE,
        )
        self.assertEqual(resultado.cuit_detectado, "30718078063")

    def test_cuit_distintos_son_cuit_diferente(self) -> None:
        resultado = self._comparar(
            cuit_detectado="30699999991"
        )

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.CUIT_DIFERENTE,
        )

    def test_cuit_detectado_none_no_es_verificable(self) -> None:
        resultado = self._comparar(cuit_detectado=None)

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.NO_VERIFICABLE,
        )
        self.assertIsNone(resultado.cuit_detectado)

    def test_cuit_detectado_vacio_no_es_verificable(self) -> None:
        resultado = self._comparar(cuit_detectado=" ")

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.NO_VERIFICABLE,
        )

    def test_cuit_detectado_invalido_no_es_verificable(
        self,
    ) -> None:
        resultado = self._comparar(
            cuit_detectado="30-71807806"
        )

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.NO_VERIFICABLE,
        )

    def test_misma_razon_social_no_advierte(self) -> None:
        resultado = self._comparar()

        self.assertEqual(resultado.advertencias, ())

    def test_ignora_mayusculas_en_razon_social(self) -> None:
        resultado = self._comparar(
            razon_social_detectada=(
                "constructora del sur s.r.l."
            )
        )

        self.assertEqual(resultado.advertencias, ())

    def test_considera_equivalentes_sa_y_s_a(self) -> None:
        resultado = self._comparar(
            proveedor_razon_social="Servicios del Sur S.A.",
            razon_social_detectada="Servicios del Sur SA",
        )

        self.assertEqual(resultado.advertencias, ())

    def test_considera_equivalentes_srl_y_s_r_l(self) -> None:
        resultado = self._comparar(
            proveedor_razon_social="Constructora del Sur S.R.L.",
            razon_social_detectada="Constructora del Sur SRL",
        )

        self.assertEqual(resultado.advertencias, ())

    def test_advierte_razon_social_materialmente_diferente(
        self,
    ) -> None:
        resultado = self._comparar(
            razon_social_detectada="Otra Empresa S.R.L."
        )

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.COINCIDE,
        )
        self.assertEqual(
            resultado.advertencias,
            (ADVERTENCIA_RAZON_SOCIAL_DIFERENTE,),
        )

    def test_advierte_razon_social_detectada_ausente(
        self,
    ) -> None:
        resultado = self._comparar(
            razon_social_detectada=None
        )

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.COINCIDE,
        )
        self.assertEqual(
            resultado.advertencias,
            (ADVERTENCIA_RAZON_SOCIAL_NO_VERIFICABLE,),
        )

    def test_cuit_diferente_prevalece_sobre_razon_social(
        self,
    ) -> None:
        resultado = self._comparar(
            cuit_detectado="30699999991",
            razon_social_detectada=(
                "Constructora del Sur S.R.L."
            ),
        )

        self.assertEqual(
            resultado.estado,
            EstadoControlProveedorOP.CUIT_DIFERENTE,
        )
        self.assertEqual(resultado.advertencias, ())

    def test_rechaza_proveedor_cuit_no_textual(self) -> None:
        with self.assertRaises(TypeError):
            self._comparar(proveedor_cuit=None)

    def test_rechaza_proveedor_cuit_invalido(self) -> None:
        with self.assertRaises(ValueError):
            self._comparar(proveedor_cuit="30-71807806")

    def test_rechaza_proveedor_razon_social_vacia(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            self._comparar(proveedor_razon_social=" ")

    def test_rechaza_cuit_detectado_no_textual(self) -> None:
        with self.assertRaises(TypeError):
            self._comparar(cuit_detectado=30718078063)

    def test_rechaza_razon_social_detectada_no_textual(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            self._comparar(razon_social_detectada=123)

    def test_es_determinista_para_las_mismas_entradas(
        self,
    ) -> None:
        argumentos = {
            "proveedor_cuit": "30718078063",
            "proveedor_razon_social": (
                "Constructora del Sur S.R.L."
            ),
            "cuit_detectado": "30-71807806-3",
            "razon_social_detectada": (
                "Otra Empresa S.R.L."
            ),
        }

        primer_resultado = comparar_proveedor_op(**argumentos)
        segundo_resultado = comparar_proveedor_op(**argumentos)

        self.assertEqual(primer_resultado, segundo_resultado)

    @staticmethod
    def _comparar(
        *,
        proveedor_cuit: str = "30718078063",
        proveedor_razon_social: str = (
            "Constructora del Sur S.R.L."
        ),
        cuit_detectado: str | None = "30718078063",
        razon_social_detectada: str | None = (
            "Constructora del Sur S.R.L."
        ),
    ):
        return comparar_proveedor_op(
            proveedor_cuit=proveedor_cuit,
            proveedor_razon_social=proveedor_razon_social,
            cuit_detectado=cuit_detectado,
            razon_social_detectada=razon_social_detectada,
        )


if __name__ == "__main__":
    unittest.main()
