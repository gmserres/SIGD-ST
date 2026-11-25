import getpass
import os

from app.composition.auth import auth_service
from app.domain.roles import RolUsuario
from app.schemas.auth import UsuarioCreate
from app.services.auth import EmailDuplicadoError


def main() -> None:
    nombre = (os.getenv("SIGD_ST_ADMIN_NOMBRE") or input("Nombre del administrador: ")).strip()
    email = (os.getenv("SIGD_ST_ADMIN_EMAIL") or input("Correo del administrador: ")).strip().lower()
    password = os.getenv("SIGD_ST_ADMIN_PASSWORD") or getpass.getpass("Contraseña (mínimo 12 caracteres): ")
    try:
        usuario = auth_service.crear_usuario(UsuarioCreate(
            nombre=nombre, email=email, password=password, rol=RolUsuario.ADMINISTRADOR
        ))
    except EmailDuplicadoError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Administrador creado: {usuario.email}")


if __name__ == "__main__":
    main()
