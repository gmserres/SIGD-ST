from datetime import date

from pydantic import BaseModel


class FormalizacionDisposicionCreate(BaseModel):
    fecha_formalizacion: date
