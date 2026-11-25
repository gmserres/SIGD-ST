import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.passwords import hash_password, verify_password
from app.domain.roles import RolUsuario
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.usuario_model import SesionUsuarioModel, UsuarioModel
from app.schemas.auth import UsuarioCreate
from app.services.auth import AuthService, CredencialesInvalidasError, EmailDuplicadoError


class PasswordTest(unittest.TestCase):
    def test_hash_no_expone_password_y_verifica(self):
        encoded = hash_password("Frase segura 2026!")
        self.assertNotIn("Frase segura 2026!", encoded)
        self.assertTrue(verify_password("Frase segura 2026!", encoded))
        self.assertFalse(verify_password("incorrecta", encoded))

    def test_rechaza_password_corta(self):
        with self.assertRaises(ValueError):
            hash_password("corta")


class AuthServiceTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.service = AuthService(self.factory)
        self.data = UsuarioCreate(
            nombre="Administración",
            email="admin@consejo.local",
            rol=RolUsuario.ADMINISTRADOR,
            password="Frase segura 2026!",
        )

    def test_crea_autentica_y_resuelve_sesion(self):
        creado = self.service.crear_usuario(self.data)
        token, expires_in, autenticado = self.service.autenticar(
            self.data.email, self.data.password
        )
        self.assertEqual(creado.id, autenticado.id)
        self.assertEqual(8 * 3600, expires_in)
        self.assertEqual(creado.id, self.service.usuario_por_token(token).id)
        self.service.cerrar_sesion(token)
        self.assertIsNone(self.service.usuario_por_token(token))

    def test_no_guarda_token_en_claro(self):
        self.service.crear_usuario(self.data)
        token, _, _ = self.service.autenticar(self.data.email, self.data.password)
        with self.factory() as session:
            stored = session.query(SesionUsuarioModel).one()
            self.assertNotEqual(token, stored.token_hash)
            self.assertEqual(64, len(stored.token_hash))

    def test_credenciales_invalidas_no_distinguen_causa(self):
        self.service.crear_usuario(self.data)
        with self.assertRaises(CredencialesInvalidasError):
            self.service.autenticar(self.data.email, "Password incorrecta")
        with self.assertRaises(CredencialesInvalidasError):
            self.service.autenticar("nadie@consejo.local", "Password incorrecta")

    def test_email_es_unico(self):
        self.service.crear_usuario(self.data)
        with self.assertRaises(EmailDuplicadoError):
            self.service.crear_usuario(self.data)

    def test_desactivar_revoca_sesiones(self):
        user = self.service.crear_usuario(self.data)
        token, _, _ = self.service.autenticar(self.data.email, self.data.password)
        actualizado = self.service.actualizar_estado(user.id, False)
        self.assertFalse(actualizado.activo)
        self.assertIsNone(self.service.usuario_por_token(token))
        with self.assertRaises(CredencialesInvalidasError):
            self.service.autenticar(self.data.email, self.data.password)


if __name__ == "__main__":
    unittest.main()
