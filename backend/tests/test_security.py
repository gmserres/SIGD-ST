import unittest
from datetime import datetime

from fastapi import HTTPException
from starlette.requests import Request

from app.core.security import autorizar_operacion, requerir_administrador
from app.domain.roles import RolUsuario
from app.schemas.auth import UsuarioRead


def usuario(rol: RolUsuario) -> UsuarioRead:
    return UsuarioRead(
        id=f"user-{rol.value}", nombre="Prueba", email="prueba@consejo.local",
        rol=rol, activo=True, creado_en=datetime(2026, 11, 10),
    )


def request(method: str, path: str) -> Request:
    return Request({"type": "http", "method": method, "path": path, "headers": []})


class AutorizacionTest(unittest.TestCase):
    def test_consulta_solo_puede_leer(self):
        consulta = usuario(RolUsuario.CONSULTA)
        self.assertEqual(consulta, autorizar_operacion(request("GET", "/expedientes"), consulta))
        with self.assertRaises(HTTPException) as ctx:
            autorizar_operacion(request("POST", "/expedientes"), consulta)
        self.assertEqual(403, ctx.exception.status_code)

    def test_operador_no_realiza_actos_sensibles(self):
        operador = usuario(RolUsuario.OPERADOR)
        self.assertEqual(operador, autorizar_operacion(request("POST", "/expedientes"), operador))
        for path in ("/expedientes/X/validar", "/expedientes/X/cierre", "/expedientes/administracion/parametros"):
            with self.assertRaises(HTTPException):
                autorizar_operacion(request("POST", path), operador)

    def test_secretario_puede_realizar_actos_sensibles(self):
        secretario = usuario(RolUsuario.SECRETARIO_TECNICO)
        self.assertEqual(
            secretario, autorizar_operacion(request("POST", "/expedientes/X/cierre"), secretario)
        )

    def test_solo_administrador_gestiona_usuarios(self):
        admin = usuario(RolUsuario.ADMINISTRADOR)
        self.assertEqual(admin, requerir_administrador(admin))
        with self.assertRaises(HTTPException) as ctx:
            requerir_administrador(usuario(RolUsuario.SECRETARIO_TECNICO))
        self.assertEqual(403, ctx.exception.status_code)


if __name__ == "__main__":
    unittest.main()
