from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.domain.habilitacion_proveedor_op import (
    EstadoHabilitacionProveedorOP,
)


class DisposicionRead(BaseModel):
    expediente_id: str
    documento_op_id: str | None = None
    control_proveedor_op_id: str | None = None
    seleccion_proveedor_id: str | None = None
    proveedor_definitivo_id: str | None = None
    proveedor_definitivo_cuit: str | None = None
    proveedor_definitivo_razon_social: str | None = None
    estado_habilitacion_actual: EstadoHabilitacionProveedorOP | None = None
    obsoleto: bool = False
    numero_disposicion: str | None
    estado: str
    visto: str
    considerando: str
    dispone: str
    observaciones_ia: list[str]
    creado: datetime
    actualizado: datetime


class DisposicionUpdate(BaseModel):
    visto: str | None = None
    considerando: str | None = None
    dispone: str | None = None


class DisposicionEmitirCreate(BaseModel):
    numero_disposicion: str = Field(min_length=1, max_length=255)


class DisposicionEmitidaRead(BaseModel):
    id_disposicion: str
    expediente_id: str
    documento_op_id: str | None = None
    control_proveedor_op_id: str | None = None
    seleccion_proveedor_id: str | None = None
    proveedor_definitivo_id: str | None = None
    proveedor_definitivo_cuit: str | None = None
    proveedor_definitivo_razon_social: str | None = None
    configuracion_uc_id: str
    numero_disposicion: str
    fecha_emision: datetime
    fondo_interviniente: str
    numero_op: str
    numero_liquidacion: str | None
    proveedor: str
    cuit: str
    importe: Decimal
    objeto: str
    establecimiento: str
    valor_uc_aplicado: Decimal
    cantidad_uc: Decimal
    procedimiento_contratacion: str
    norma_uc: str
    texto_emitido: str
    ruta_docx: str
