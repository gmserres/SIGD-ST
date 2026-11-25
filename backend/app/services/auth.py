from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session

from app.core.passwords import hash_password, hash_session_token, new_session_token, verify_password
from app.domain.roles import RolUsuario
from app.infrastructure.database.models.usuario_model import SesionUsuarioModel, UsuarioModel
from app.schemas.auth import UsuarioCreate, UsuarioRead


SESSION_HOURS = 8


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class CredencialesInvalidasError(Exception):
    pass


class EmailDuplicadoError(Exception):
    pass


class AuthService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    @staticmethod
    def _read(model: UsuarioModel) -> UsuarioRead:
        return UsuarioRead(
            id=model.id,
            nombre=model.nombre,
            email=model.email,
            rol=RolUsuario(model.rol),
            activo=model.activo,
            creado_en=model.creado_en,
        )

    def crear_usuario(self, data: UsuarioCreate) -> UsuarioRead:
        now = _utcnow()
        model = UsuarioModel(
            id=str(uuid4()), nombre=data.nombre, email=data.email, rol=data.rol.value,
            password_hash=hash_password(data.password), activo=True,
            creado_en=now, actualizado_en=now,
        )
        with self._session_factory() as session:
            session.add(model)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise EmailDuplicadoError("Ya existe un usuario con ese correo electrónico.") from exc
            return self._read(model)

    def listar_usuarios(self) -> list[UsuarioRead]:
        with self._session_factory() as session:
            models = session.scalars(select(UsuarioModel).order_by(UsuarioModel.nombre)).all()
            return [self._read(model) for model in models]

    def autenticar(self, email: str, password: str) -> tuple[str, int, UsuarioRead]:
        with self._session_factory() as session:
            user = session.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
            if user is None or not user.activo or not verify_password(password, user.password_hash):
                raise CredencialesInvalidasError("Credenciales inválidas.")
            raw_token = new_session_token()
            now = _utcnow()
            session.add(SesionUsuarioModel(
                token_hash=hash_session_token(raw_token), usuario_id=user.id,
                creada_en=now, expira_en=now + timedelta(hours=SESSION_HOURS), revocada_en=None,
            ))
            session.commit()
            return raw_token, SESSION_HOURS * 3600, self._read(user)

    def usuario_por_token(self, token: str) -> UsuarioRead | None:
        now = _utcnow()
        with self._session_factory() as session:
            row = session.execute(
                select(SesionUsuarioModel, UsuarioModel)
                .join(UsuarioModel, UsuarioModel.id == SesionUsuarioModel.usuario_id)
                .where(
                    SesionUsuarioModel.token_hash == hash_session_token(token),
                    SesionUsuarioModel.revocada_en.is_(None),
                    SesionUsuarioModel.expira_en > now,
                    UsuarioModel.activo.is_(True),
                )
            ).first()
            return self._read(row[1]) if row else None

    def cerrar_sesion(self, token: str) -> None:
        with self._session_factory() as session:
            session.execute(
                update(SesionUsuarioModel)
                .where(SesionUsuarioModel.token_hash == hash_session_token(token))
                .values(revocada_en=_utcnow())
            )
            session.commit()

    def actualizar_estado(self, usuario_id: str, activo: bool) -> UsuarioRead:
        with self._session_factory() as session:
            user = session.get(UsuarioModel, usuario_id)
            if user is None:
                raise KeyError(usuario_id)
            user.activo = activo
            user.actualizado_en = _utcnow()
            if not activo:
                session.execute(
                    update(SesionUsuarioModel)
                    .where(SesionUsuarioModel.usuario_id == usuario_id, SesionUsuarioModel.revocada_en.is_(None))
                    .values(revocada_en=_utcnow())
                )
            session.commit()
            return self._read(user)
