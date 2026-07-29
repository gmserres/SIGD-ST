from datetime import datetime

from app.infrastructure.database.models.documento_model import (
    DocumentoModel,
)
from app.schemas.documento import DocumentoCreate, DocumentoRead


def a_modelo(
    expediente_id: str,
    data: DocumentoCreate,
    fecha_carga: datetime,
) -> DocumentoModel:
    return DocumentoModel(
        expediente_id=expediente_id,
        tipo=data.tipo,
        nombre_archivo=data.nombre_archivo,
        ruta=data.ruta,
        fecha_carga=fecha_carga,
        observaciones=data.observaciones,
        tamano_bytes=data.tamano_bytes,
        mime_type=data.mime_type,
    )


def a_schema(modelo: DocumentoModel) -> DocumentoRead:
    return DocumentoRead(
        id=modelo.id,
        expediente_id=modelo.expediente_id,
        tipo=modelo.tipo,
        nombre_archivo=modelo.nombre_archivo,
        ruta=modelo.ruta,
        fecha_carga=modelo.fecha_carga,
        observaciones=modelo.observaciones,
        tamano_bytes=modelo.tamano_bytes,
        mime_type=modelo.mime_type,
    )
