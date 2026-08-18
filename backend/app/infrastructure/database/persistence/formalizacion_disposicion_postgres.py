from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.disposicion import Disposicion
from app.infrastructure.database.mappers.disposicion_mapper import a_dominio
from app.infrastructure.database.models.disposicion_model import DisposicionModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.repositories.formalizacion_disposicion_persistence import (
    DisposicionNoEncontradaAlFormalizarError,
    DisposicionYaFormalizadaError,
    ExpedienteDisposicionNoEncontradoError,
    FechaFormalizacionAnteriorAEmisionError,
)


class PostgresFormalizacionDisposicionPersistence:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def formalizar(
        self,
        id_disposicion: str,
        fecha_formalizacion: date,
        usuario_registro: str,
        registrado_en: datetime,
    ) -> Disposicion:
        with self._session_factory() as session:
            try:
                modelo = session.scalar(
                    select(DisposicionModel)
                    .where(DisposicionModel.id_disposicion == id_disposicion)
                    .with_for_update()
                )
                if modelo is None:
                    raise DisposicionNoEncontradaAlFormalizarError(
                        id_disposicion
                    )
                expediente = session.scalar(
                    select(ExpedienteModel).where(
                        ExpedienteModel.id == modelo.expediente_id
                    )
                )
                if expediente is None:
                    raise ExpedienteDisposicionNoEncontradoError(
                        modelo.expediente_id
                    )
                metadatos = (
                    modelo.fecha_formalizacion,
                    modelo.usuario_registro_formalizacion,
                    modelo.registrado_formalizacion_en,
                )
                if any(valor is not None for valor in metadatos):
                    raise DisposicionYaFormalizadaError(id_disposicion)
                if fecha_formalizacion < modelo.fecha_emision.date():
                    raise FechaFormalizacionAnteriorAEmisionError(
                        id_disposicion
                    )

                modelo.fecha_formalizacion = fecha_formalizacion
                modelo.usuario_registro_formalizacion = usuario_registro
                modelo.registrado_formalizacion_en = registrado_en
                session.flush()
                resultado = a_dominio(modelo)
                session.commit()
                return resultado
            except Exception:
                session.rollback()
                raise
