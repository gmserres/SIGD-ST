from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.mappers.checklist_fisico_mapper import (
    a_modelo,
    a_schema,
    actualizar_modelo,
)
from app.infrastructure.database.models.checklist_fisico_model import (
    ChecklistFisicoModel,
)
from app.schemas.checklist_fisico import ChecklistFisicoRead


class PostgresChecklistFisicoRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def obtener_por_expediente(
        self,
        expediente_id: str,
    ) -> ChecklistFisicoRead | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ChecklistFisicoModel).where(
                    ChecklistFisicoModel.expediente_id
                    == expediente_id
                )
            )
            return a_schema(modelo) if modelo is not None else None

    def guardar(
        self,
        checklist: ChecklistFisicoRead,
    ) -> ChecklistFisicoRead:
        with self._session_factory() as session:
            try:
                modelo = session.scalar(
                    select(ChecklistFisicoModel).where(
                        ChecklistFisicoModel.expediente_id
                        == checklist.expediente_id
                    )
                )
                if modelo is None:
                    modelo = a_modelo(checklist)
                    session.add(modelo)
                else:
                    actualizar_modelo(modelo, checklist)

                session.flush()
                guardado = a_schema(modelo)
                session.commit()
                return guardado
            except Exception:
                session.rollback()
                raise
