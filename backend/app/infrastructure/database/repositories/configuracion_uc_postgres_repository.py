from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.domain.configuracion_uc import ConfiguracionUC, ConfiguracionUCId
from app.infrastructure.database.mappers.configuracion_uc_mapper import (
    a_dominio,
    a_modelo,
    actualizar_modelo,
)
from app.infrastructure.database.models.configuracion_uc_model import (
    ConfiguracionUCModel,
)


class PostgresConfiguracionUCRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(self, configuracion: ConfiguracionUC) -> None:
        with self._session_factory() as session:
            try:
                modelo = session.scalar(
                    select(ConfiguracionUCModel)
                    .options(
                        selectinload(ConfiguracionUCModel.rangos)
                    )
                    .where(
                        ConfiguracionUCModel.id_configuracion
                        == configuracion.id_configuracion
                    )
                )
                if modelo is None:
                    session.add(a_modelo(configuracion))
                else:
                    actualizar_modelo(modelo, configuracion)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(
        self,
        configuracion_id: ConfiguracionUCId,
    ) -> ConfiguracionUC | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ConfiguracionUCModel)
                .options(selectinload(ConfiguracionUCModel.rangos))
                .where(
                    ConfiguracionUCModel.id_configuracion
                    == configuracion_id
                )
            )
            if modelo is None:
                return None
            return a_dominio(modelo)

    def listar(self) -> list[ConfiguracionUC]:
        with self._session_factory() as session:
            consulta = (
                select(ConfiguracionUCModel)
                .options(selectinload(ConfiguracionUCModel.rangos))
                .order_by(
                    ConfiguracionUCModel.fecha_inicio_vigencia,
                    ConfiguracionUCModel.id_configuracion,
                )
            )
            modelos = session.scalars(consulta).all()
            return [a_dominio(modelo) for modelo in modelos]

    def buscar_vigentes_para_fecha(
        self,
        fecha: date,
    ) -> list[ConfiguracionUC]:
        with self._session_factory() as session:
            consulta = (
                select(ConfiguracionUCModel)
                .options(selectinload(ConfiguracionUCModel.rangos))
                .where(
                    ConfiguracionUCModel.fecha_inicio_vigencia <= fecha,
                    or_(
                        ConfiguracionUCModel.fecha_fin_vigencia.is_(None),
                        ConfiguracionUCModel.fecha_fin_vigencia >= fecha,
                    ),
                )
                .order_by(
                    ConfiguracionUCModel.fecha_inicio_vigencia,
                    ConfiguracionUCModel.id_configuracion,
                )
            )
            modelos = session.scalars(consulta).all()
            return [a_dominio(modelo) for modelo in modelos]
