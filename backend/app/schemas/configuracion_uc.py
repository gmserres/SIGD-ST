from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.configuracion_uc import (
    ConfiguracionUCId,
    RangoProcedimientoUCId,
)


class RangoProcedimientoUCSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_rango: RangoProcedimientoUCId
    configuracion_uc_id: ConfiguracionUCId
    limite_inferior: Decimal
    limite_superior: Decimal
    limite_inferior_inclusivo: bool
    limite_superior_inclusivo: bool
    procedimiento: str
    articulo: str
    inciso: str
    referencia_normativa: str


class ConfiguracionUCSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_configuracion: ConfiguracionUCId
    fecha_inicio_vigencia: date
    fecha_fin_vigencia: date | None
    valor_uc: Decimal
    moneda: str
    resolucion: str
    organismo_emisor: str
    estado: str
    rangos: tuple[RangoProcedimientoUCSchema, ...]
