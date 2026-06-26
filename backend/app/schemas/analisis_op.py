from typing import List, Optional

from pydantic import BaseModel


class DocumentoComercialExtraido(BaseModel):
    tipo: str
    letra: str
    numero: str
    fecha: str
    importe: float


class RetencionExtraida(BaseModel):
    concepto: str
    importe: float


class AnalisisOPRead(BaseModel):
    expediente_id: str
    modo: str
    op_detectada: bool
    proveedor: Optional[str]
    cuit: Optional[str]
    fondo: Optional[str]
    orden_pago: Optional[str]
    liquidacion: Optional[str]
    fecha_op: Optional[str]
    importe_bruto: Optional[float]
    importe_neto: Optional[float]
    valor_uc: float
    norma_uc: str
    cantidad_uc: Optional[float]
    procedimiento: Optional[str]
    encuadre_legal: Optional[str]
    documentos_comerciales: List[DocumentoComercialExtraido]
    retenciones: List[RetencionExtraida]
    validaciones: List[str]
    advertencias: List[str]
    faltantes: List[str]
