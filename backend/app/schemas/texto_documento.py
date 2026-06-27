from pydantic import BaseModel


class TextoDocumentoRead(BaseModel):
    expediente_id: str
    documento_id: str
    nombre_archivo: str
    paginas: int
    caracteres: int
    texto: str
    advertencias: list[str]
