from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.composition.auth import auth_service
from app.core.security import requerir_administrador, token_actual, usuario_actual
from app.schemas.auth import (
    LoginCreate, TokenRead, UsuarioCreate, UsuarioEstadoUpdate, UsuarioRead,
)
from app.services.auth import CredencialesInvalidasError, EmailDuplicadoError


router = APIRouter()


@router.post("/login", response_model=TokenRead)
def login(data: LoginCreate):
    try:
        token, expires_in, usuario = auth_service.autenticar(data.email, data.password)
    except CredencialesInvalidasError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenRead(access_token=token, expires_in=expires_in, usuario=usuario)


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Annotated[UsuarioRead, Depends(usuario_actual)]):
    return usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: Annotated[str, Depends(token_actual)]):
    auth_service.cerrar_sesion(token)


@router.get("/usuarios", response_model=list[UsuarioRead])
def listar_usuarios(_admin: Annotated[UsuarioRead, Depends(requerir_administrador)]):
    return auth_service.listar_usuarios()


@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: UsuarioCreate,
    _admin: Annotated[UsuarioRead, Depends(requerir_administrador)],
):
    try:
        return auth_service.crear_usuario(data)
    except EmailDuplicadoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/usuarios/{usuario_id}/estado", response_model=UsuarioRead)
def actualizar_estado_usuario(
    usuario_id: str,
    data: UsuarioEstadoUpdate,
    admin: Annotated[UsuarioRead, Depends(requerir_administrador)],
):
    if usuario_id == admin.id and not data.activo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No puede desactivar su propia cuenta.")
    try:
        return auth_service.actualizar_estado(usuario_id, data.activo)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.") from exc
