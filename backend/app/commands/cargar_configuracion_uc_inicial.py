import sys

from app.application.configuracion_uc.registrar_configuracion_uc import (
    RegistrarConfiguracionUC,
)
from app.application.initial_data.configuracion_uc_strategy import (
    EstrategiaCargaInicialConfiguracionUC,
)
from app.infrastructure.database.repositories.configuracion_uc_postgres_repository import (
    PostgresConfiguracionUCRepository,
)
from app.infrastructure.database.session import (
    crear_fabrica_sesiones,
    crear_motor,
)
from app.initial_data.carga_inicial import (
    CargaInicialDivergenteError,
    ResultadoCargaInicial,
    ejecutar_carga_inicial,
)
from app.initial_data.configuracion_uc_inicial import (
    DatosNormativosPendientesError,
    crear_configuracion_uc_inicial,
)


NOMBRE_CARGA = "Configuración UC inicial"


def main() -> int:
    try:
        configuracion = crear_configuracion_uc_inicial()
    except DatosNormativosPendientesError as error:
        print(
            "No se puede ejecutar la carga inicial: "
            "existen datos normativos pendientes de confirmación.",
            file=sys.stderr,
        )
        print(str(error), file=sys.stderr)
        return 2
    except ValueError as error:
        print(
            f"Error de validación de la carga inicial: {error}",
            file=sys.stderr,
        )
        return 2

    try:
        engine = crear_motor()
        session_factory = crear_fabrica_sesiones(engine)
        repository = PostgresConfiguracionUCRepository(session_factory)
        registrar_configuracion_uc = RegistrarConfiguracionUC(
            repository
        )
        estrategia = EstrategiaCargaInicialConfiguracionUC(
            repository,
            registrar_configuracion_uc,
        )
        resultado = ejecutar_carga_inicial(
            nombre_carga=NOMBRE_CARGA,
            dato=configuracion,
            estrategia=estrategia,
        )
    except CargaInicialDivergenteError as error:
        print(str(error), file=sys.stderr)
        return 3
    except Exception as error:
        print(
            "No fue posible persistir la carga inicial: "
            f"{type(error).__name__}.",
            file=sys.stderr,
        )
        return 1

    if resultado == ResultadoCargaInicial.CARGADA:
        print("Configuración UC inicial cargada correctamente.")
    else:
        print(
            "La Configuración UC inicial ya se encontraba cargada "
            "con datos idénticos."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
