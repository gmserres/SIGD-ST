import unittest
from datetime import date
from decimal import Decimal

from app.application.configuracion_uc.registrar_configuracion_uc import (
    ConfiguracionUCYaRegistradaError,
    RegistrarConfiguracionUC,
)
from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
    VigenciaConfiguracionUCSuperpuestaError,
)


class RepositorioConfiguracionUCSpy:
    def __init__(
        self,
        existentes: list[ConfiguracionUC] | None = None,
    ) -> None:
        self.existentes = list(existentes or [])
        self.operaciones: list[str] = []
        self.guardadas: list[ConfiguracionUC] = []
        self.error_al_obtener: Exception | None = None
        self.error_al_listar: Exception | None = None
        self.error_al_guardar: Exception | None = None

    def obtener_por_id(
        self,
        configuracion_id: str,
    ) -> ConfiguracionUC | None:
        self.operaciones.append("obtener_por_id")
        if self.error_al_obtener is not None:
            raise self.error_al_obtener
        return next(
            (
                configuracion
                for configuracion in self.existentes
                if configuracion.id_configuracion == configuracion_id
            ),
            None,
        )

    def listar(self) -> list[ConfiguracionUC]:
        self.operaciones.append("listar")
        if self.error_al_listar is not None:
            raise self.error_al_listar
        return list(self.existentes)

    def guardar(self, configuracion: ConfiguracionUC) -> None:
        self.operaciones.append("guardar")
        if self.error_al_guardar is not None:
            raise self.error_al_guardar
        self.guardadas.append(configuracion)


class RegistrarConfiguracionUCTest(unittest.TestCase):
    def test_guarda_configuracion_sin_superposicion(self) -> None:
        repository = RepositorioConfiguracionUCSpy()
        caso_de_uso = RegistrarConfiguracionUC(repository)
        configuracion = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            None,
        )

        resultado = caso_de_uso.ejecutar(configuracion)

        self.assertEqual(resultado, configuracion)
        self.assertEqual(repository.guardadas, [configuracion])
        self.assertEqual(
            repository.operaciones,
            ["obtener_por_id", "listar", "guardar"],
        )

    def test_rechaza_configuracion_superpuesta(self) -> None:
        existente = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            date(2026, 6, 30),
        )
        repository = RepositorioConfiguracionUCSpy([existente])
        caso_de_uso = RegistrarConfiguracionUC(repository)
        nueva = self._crear_configuracion(
            "configuracion-2",
            date(2026, 6, 30),
            None,
        )

        with self.assertRaises(
            VigenciaConfiguracionUCSuperpuestaError
        ):
            caso_de_uso.ejecutar(nueva)

        self.assertEqual(repository.guardadas, [])
        self.assertEqual(
            repository.operaciones,
            ["obtener_por_id", "listar"],
        )

    def test_admite_configuraciones_consecutivas(self) -> None:
        existente = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            date(2026, 6, 30),
        )
        repository = RepositorioConfiguracionUCSpy([existente])
        caso_de_uso = RegistrarConfiguracionUC(repository)
        nueva = self._crear_configuracion(
            "configuracion-2",
            date(2026, 7, 1),
            None,
        )

        caso_de_uso.ejecutar(nueva)

        self.assertEqual(repository.guardadas, [nueva])

    def test_admite_varias_configuraciones_en_el_mismo_anio(
        self,
    ) -> None:
        existente = self._crear_configuracion(
            "configuracion-1",
            date(2026, 2, 1),
            date(2026, 3, 31),
        )
        repository = RepositorioConfiguracionUCSpy([existente])
        caso_de_uso = RegistrarConfiguracionUC(repository)
        nueva = self._crear_configuracion(
            "configuracion-2",
            date(2026, 4, 1),
            date(2026, 12, 31),
        )

        caso_de_uso.ejecutar(nueva)

        self.assertEqual(repository.guardadas, [nueva])

    def test_rechaza_identidad_tecnica_ya_registrada(self) -> None:
        existente = self._crear_configuracion(
            "configuracion-1",
            date(2026, 1, 1),
            None,
        )
        repository = RepositorioConfiguracionUCSpy([existente])
        caso_de_uso = RegistrarConfiguracionUC(repository)

        with self.assertRaises(ConfiguracionUCYaRegistradaError):
            caso_de_uso.ejecutar(existente)

        self.assertEqual(repository.guardadas, [])
        self.assertEqual(repository.operaciones, ["obtener_por_id"])

    def test_propaga_error_al_obtener_por_id(self) -> None:
        repository = RepositorioConfiguracionUCSpy()
        repository.error_al_obtener = RuntimeError("Error al obtener.")
        caso_de_uso = RegistrarConfiguracionUC(repository)

        with self.assertRaisesRegex(RuntimeError, "Error al obtener"):
            caso_de_uso.ejecutar(
                self._crear_configuracion(
                    "configuracion-1",
                    date(2026, 1, 1),
                    None,
                )
            )

        self.assertEqual(repository.guardadas, [])

    def test_propaga_error_al_listar(self) -> None:
        repository = RepositorioConfiguracionUCSpy()
        repository.error_al_listar = RuntimeError("Error al listar.")
        caso_de_uso = RegistrarConfiguracionUC(repository)

        with self.assertRaisesRegex(RuntimeError, "Error al listar"):
            caso_de_uso.ejecutar(
                self._crear_configuracion(
                    "configuracion-1",
                    date(2026, 1, 1),
                    None,
                )
            )

        self.assertEqual(repository.guardadas, [])

    def test_propaga_error_al_guardar(self) -> None:
        repository = RepositorioConfiguracionUCSpy()
        repository.error_al_guardar = RuntimeError(
            "Error al guardar."
        )
        caso_de_uso = RegistrarConfiguracionUC(repository)

        with self.assertRaisesRegex(RuntimeError, "Error al guardar"):
            caso_de_uso.ejecutar(
                self._crear_configuracion(
                    "configuracion-1",
                    date(2026, 1, 1),
                    None,
                )
            )

        self.assertEqual(
            repository.operaciones,
            ["obtener_por_id", "listar", "guardar"],
        )

    @staticmethod
    def _crear_configuracion(
        configuracion_id: str,
        fecha_inicio: date,
        fecha_fin: date | None,
    ) -> ConfiguracionUC:
        return ConfiguracionUC(
            id_configuracion=configuracion_id,
            fecha_inicio_vigencia=fecha_inicio,
            fecha_fin_vigencia=fecha_fin,
            valor_uc=Decimal("1000"),
            moneda="MONEDA_DE_PRUEBA",
            resolucion=f"Resolución {configuracion_id}",
            organismo_emisor="ORGANISMO_DE_PRUEBA",
            estado="ESTADO_DE_PRUEBA",
            rangos=(
                RangoProcedimientoUC(
                    id_rango=f"{configuracion_id}-rango",
                    configuracion_uc_id=configuracion_id,
                    limite_inferior=Decimal("0"),
                    limite_superior=Decimal("100"),
                    limite_inferior_inclusivo=True,
                    limite_superior_inclusivo=True,
                    procedimiento="PROCEDIMIENTO_DE_PRUEBA",
                    articulo="ARTICULO_DE_PRUEBA",
                    inciso="INCISO_DE_PRUEBA",
                    referencia_normativa="REFERENCIA_DE_PRUEBA",
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
