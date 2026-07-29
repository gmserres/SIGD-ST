from datetime import date
from decimal import Decimal

from app.domain.configuracion_uc import (
    ConfiguracionUC,
    RangoProcedimientoUC,
)


CONFIGURACION_UC_INICIAL_ID = "configuracion-uc-carga-001"
ESTADO_CONFIGURACION_UC_INICIAL = "VIGENTE"

FECHA_INICIO_VIGENCIA: date | None = date(2025, 3, 13)
VALOR_UC: Decimal | None = Decimal("1677")
MONEDA: str | None = "ARS"
RESOLUCION: str | None = "Resolución OPC 54/2025"
ORGANISMO_EMISOR: str | None = "Organismo Provincial de Contrataciones"
RANGOS: tuple[RangoProcedimientoUC, ...] = (
    RangoProcedimientoUC(
        id_rango="rango-uc-factura-conformada-001",
        configuracion_uc_id=CONFIGURACION_UC_INICIAL_ID,
        limite_inferior=Decimal("0"),
        limite_superior=Decimal("10000"),
        limite_inferior_inclusivo=True,
        limite_superior_inclusivo=True,
        procedimiento="Factura Conformada",
        articulo="18",
        inciso="C",
        referencia_normativa="Ley 13.981",
    ),
    RangoProcedimientoUC(
        id_rango="rango-uc-procedimiento-abreviado-002",
        configuracion_uc_id=CONFIGURACION_UC_INICIAL_ID,
        limite_inferior=Decimal("10000"),
        limite_superior=Decimal("50000"),
        limite_inferior_inclusivo=False,
        limite_superior_inclusivo=True,
        procedimiento="Procedimiento Abreviado",
        articulo="18",
        inciso="B",
        referencia_normativa="Ley 13.981",
    ),
    RangoProcedimientoUC(
        id_rango="rango-uc-contratacion-menor-003",
        configuracion_uc_id=CONFIGURACION_UC_INICIAL_ID,
        limite_inferior=Decimal("50000"),
        limite_superior=Decimal("100000"),
        limite_inferior_inclusivo=False,
        limite_superior_inclusivo=True,
        procedimiento="Contratación menor por monto",
        articulo="18",
        inciso="A",
        referencia_normativa="Ley 13.981",
    ),
)


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
