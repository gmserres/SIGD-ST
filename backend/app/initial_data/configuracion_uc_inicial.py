from datetime import date
from decimal import Decimal

from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)


CONFIGURACION_UC_INICIAL_ID = "configuracion-uc-carga-001"
ESTADO_CONFIGURACION_UC_INICIAL = "VIGENTE"

# Datos pendientes de confirmación por la Dirección Funcional.
FECHA_INICIO_VIGENCIA: date | None = None
VALOR_UC: Decimal | None = None
MONEDA: str | None = None
RESOLUCION: str | None = None
ORGANISMO_EMISOR: str | None = None
RANGOS: tuple[RangoProcedimientoUC, ...] = ()


class DatosNormativosPendientesError(RuntimeError):
    pass


def crear_configuracion_uc_inicial() -> ConfiguracionUC:
    pendientes: list[str] = []

    if FECHA_INICIO_VIGENCIA is None:
        pendientes.append("fecha de inicio de vigencia")
    if VALOR_UC is None:
        pendientes.append("valor UC")
    if not MONEDA:
        pendientes.append("moneda")
    if not RESOLUCION:
        pendientes.append("resolución")
    if not ORGANISMO_EMISOR:
        pendientes.append("organismo emisor")
    if not RANGOS:
        pendientes.append("rangos normativos")

    if pendientes:
        raise DatosNormativosPendientesError(
            "Existen datos normativos pendientes de confirmación: "
            f"{', '.join(pendientes)}."
        )

    return ConfiguracionUC(
        id_configuracion=CONFIGURACION_UC_INICIAL_ID,
        fecha_inicio_vigencia=FECHA_INICIO_VIGENCIA,
        fecha_fin_vigencia=None,
        valor_uc=VALOR_UC,
        moneda=MONEDA,
        resolucion=RESOLUCION,
        organismo_emisor=ORGANISMO_EMISOR,
        estado=ESTADO_CONFIGURACION_UC_INICIAL,
        rangos=RANGOS,
    )
