from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.composition.auth import auth_service
from app.domain.roles import RolUsuario
from app.schemas.auth import UsuarioRead


bearer = HTTPBearer(auto_error=False)
Credenciales = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]

_ACTOS_SECRETARIO = (
    "/administracion/",
    "/validar",
    "/disposicion",
    "/formalizacion",
    "/registrar-firma",
    "/cierre",
    "/desistimiento",
    "/archivo",
)


def token_actual(credentials: Credenciales) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def usuario_actual(token: Annotated[str, Depends(token_actual)]) -> UsuarioRead:
    usuario = auth_service.usuario_por_token(token)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión es inválida o expiró.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def requerir_administrador(
    usuario: Annotated[UsuarioRead, Depends(usuario_actual)],
) -> UsuarioRead:
    if usuario.rol != RolUsuario.ADMINISTRADOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente.")
    return usuario


def autorizar_operacion(
    request: Request,
    usuario: Annotated[UsuarioRead, Depends(usuario_actual)],
) -> UsuarioRead:
    if usuario.rol in (RolUsuario.ADMINISTRADOR, RolUsuario.SECRETARIO_TECNICO):
        return usuario
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return usuario
    if usuario.rol == RolUsuario.OPERADOR and not any(
        fragmento in request.url.path for fragmento in _ACTOS_SECRETARIO
    ):
        return usuario
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente.")
