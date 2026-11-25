from app.core.settings import get_database_url
from app.infrastructure.database.session import crear_fabrica_sesiones, crear_motor
from app.services.auth import AuthService


_engine = crear_motor(get_database_url())
auth_session_factory = crear_fabrica_sesiones(_engine)
auth_service = AuthService(auth_session_factory)
