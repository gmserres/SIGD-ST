import unittest
from datetime import date

from app.schemas.parametros import ParametrosInstitucionalesUpdate
from app.services.parametros import ParametrosInstitucionalesService


class ParametrosInstitucionalesServiceTest(unittest.TestCase):
    def test_inicializa_el_ejercicio_institucional_vigente(self) -> None:
        servicio = ParametrosInstitucionalesService()

        self.assertEqual(servicio.obtener().ejercicio, date.today().year)

    def test_conserva_la_parametrizacion_administrativa_del_ejercicio(
        self,
    ) -> None:
        servicio = ParametrosInstitucionalesService()

        actualizado = servicio.actualizar(
            ParametrosInstitucionalesUpdate(ejercicio=2030)
        )

        self.assertEqual(actualizado.ejercicio, 2030)
        self.assertEqual(servicio.obtener().ejercicio, 2030)


if __name__ == "__main__":
    unittest.main()
