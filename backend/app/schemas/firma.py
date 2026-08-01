from datetime import date

from pydantic import BaseModel


class RegistroFirmaCreate(BaseModel):
    fecha_firma: date
