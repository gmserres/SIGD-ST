from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.expediente import Expediente
from app.infrastructure.database.mappers.expediente_mapper import (
    a_dominio,
    a_modelo,
    actualizar_modelo,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
    expedientes_id_sequence,
)


class PostgresExpedienteRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def siguiente_id(self) -> str:
        with self._session_factory() as session:
            numero = session.scalar(
                select(expedientes_id_sequence.next_value())
            )
            if numero is None:
                raise RuntimeError("No fue posible generar el ID del expediente.")
            return f"EXP-{numero:06d}"

    def guardar(self, expediente: Expediente) -> None:
        with self._session_factory() as session:
            try:
                modelo = session.scalar(
                    select(ExpedienteModel).where(
                        ExpedienteModel.id == expediente.id
                    )
                )
                if modelo is None:
                    session.add(a_modelo(expediente))
                else:
                    actualizar_modelo(modelo, expediente)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(self, expediente_id: str) -> Expediente | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ExpedienteModel).where(
                    ExpedienteModel.id == expediente_id
                )
            )
            return a_dominio(modelo) if modelo is not None else None

    def listar(self) -> list[Expediente]:
        with self._session_factory() as session:
            modelos = session.scalars(
                select(ExpedienteModel).order_by(ExpedienteModel.secuencia)
            ).all()
            return [a_dominio(modelo) for modelo in modelos]
