from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.disposicion import Disposicion
from app.infrastructure.database.mappers.disposicion_mapper import (
    a_dominio,
    a_modelo,
)
from app.infrastructure.database.mappers.control_proveedor_op_mapper import (
    documento_id_a_secuencia,
)
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.infrastructure.database.persistence.disposicion_conflicts import (
    traducir_integrity_error_disposicion,
    verificar_disposicion_duplicada,
)
from app.repositories.disposicion_repository import (
    DisposicionExpedienteAmbiguoError,
)
from app.infrastructure.database.persistence.mutabilidad_expediente import (
    bloquear_expediente_mutable,
)


class PostgresDisposicionRepository:
    def __init__(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        self._session_factory = session_factory

    def guardar(self, disposicion: Disposicion) -> None:
        with self._session_factory() as session:
            try:
                bloquear_expediente_mutable(session, disposicion.expediente_id)
                verificar_disposicion_duplicada(session, disposicion)
                session.add(a_modelo(disposicion))
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                error_traducido = traducir_integrity_error_disposicion(
                    exc, disposicion
                )
                if error_traducido is not None:
                    raise error_traducido from exc
                raise
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(
        self, disposicion_id: str
    ) -> Disposicion | None:
        with self._session_factory() as session:
            modelo = session.get(DisposicionModel, disposicion_id)
            return a_dominio(modelo) if modelo is not None else None

    def obtener_por_expediente(
        self, expediente_id: str
    ) -> Disposicion | None:
        disposiciones = self.listar_por_expediente(expediente_id)
        if len(disposiciones) > 1:
            raise DisposicionExpedienteAmbiguoError(expediente_id)
        return disposiciones[0] if disposiciones else None

    def listar_por_expediente(
        self, expediente_id: str
    ) -> list[Disposicion]:
        with self._session_factory() as session:
            modelos = session.scalars(
                select(DisposicionModel)
                .where(DisposicionModel.expediente_id == expediente_id)
                .order_by(
                    DisposicionModel.fecha_emision,
                    DisposicionModel.id_disposicion,
                )
            ).all()
            return [a_dominio(modelo) for modelo in modelos]

    def obtener_por_documento_op(
        self, documento_op_id: str
    ) -> Disposicion | None:
        return self._obtener_por(
            DisposicionModel.documento_op_secuencia,
            documento_id_a_secuencia(documento_op_id),
        )

    def obtener_por_numero(
        self, numero_disposicion: str
    ) -> Disposicion | None:
        return self._obtener_por(
            DisposicionModel.numero_disposicion,
            numero_disposicion,
        )

    def _obtener_por(self, columna, valor) -> Disposicion | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(DisposicionModel).where(columna == valor)
            )
            return a_dominio(modelo) if modelo is not None else None
