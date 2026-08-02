from datetime import date

from pydantic import BaseModel


class RegistroArchivoCreate(BaseModel):
    fecha_archivo: date
