from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_database_url


def crear_motor(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    if not url:
        raise RuntimeError(
            "La variable SIGD_ST_DATABASE_URL no está configurada."
        )

    return create_engine(
        url,
        pool_pre_ping=True,
    )


def crear_fabrica_sesiones(
    engine: Engine,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
