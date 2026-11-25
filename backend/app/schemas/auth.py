from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.roles import RolUsuario


class LoginCreate(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not value or "@" not in value:
            raise ValueError("El correo electrónico no es válido.")
        return value


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=255)
    email: str = Field(max_length=320)
    rol: RolUsuario
    password: str = Field(min_length=12, max_length=1024)

    @field_validator("nombre")
    @classmethod
    def limpiar_nombre(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El nombre es obligatorio.")
        return value

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not value or "@" not in value:
            raise ValueError("El correo electrónico no es válido.")
        return value


class UsuarioRead(BaseModel):
    id: str
    nombre: str
    email: str
    rol: RolUsuario
    activo: bool
    creado_en: datetime


class UsuarioEstadoUpdate(BaseModel):
    activo: bool


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioRead
