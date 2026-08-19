from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.seleccion_proveedor import SeleccionProveedor, SeleccionProveedorVigenteError
from app.infrastructure.database.mappers.seleccion_proveedor_mapper import a_dominio, a_modelo
from app.infrastructure.database.models.seleccion_proveedor_model import SeleccionProveedorModel
from app.infrastructure.database.persistence.mutabilidad_expediente import (
    bloquear_expediente_mutable,
)


class PostgresSeleccionProveedorRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def guardar(self, seleccion: SeleccionProveedor) -> None:
        with self._session_factory() as session:
            try:
                bloquear_expediente_mutable(session, seleccion.expediente_id)
                session.add(a_modelo(seleccion))
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                self._traducir_integridad(exc)
                raise

    def reemplazar(self, anterior: SeleccionProveedor, nueva: SeleccionProveedor) -> None:
        with self._session_factory() as session:
            try:
                bloquear_expediente_mutable(session, anterior.expediente_id)
                modelo_anterior = session.scalar(
                    select(SeleccionProveedorModel)
                    .where(
                        SeleccionProveedorModel.id_seleccion
                        == anterior.id_seleccion
                    )
                    .with_for_update()
                )
                if (
                    modelo_anterior is None
                    or not modelo_anterior.vigente
                    or modelo_anterior.expediente_id
                    != anterior.expediente_id
                ):
                    raise SeleccionProveedorVigenteError(
                        "La selección vigente cambió antes del reemplazo."
                    )
                modelo_anterior.vigente = False
                session.flush()
                session.add(a_modelo(nueva))
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                self._traducir_integridad(exc)
                raise
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(self, seleccion_id: str) -> SeleccionProveedor | None:
        with self._session_factory() as session:
            modelo = session.get(SeleccionProveedorModel, seleccion_id)
            return None if modelo is None else a_dominio(modelo)

    def obtener_vigente_por_expediente(self, expediente_id: str) -> SeleccionProveedor | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(SeleccionProveedorModel).where(
                    SeleccionProveedorModel.expediente_id == expediente_id,
                    SeleccionProveedorModel.vigente.is_(True),
                )
            )
            return None if modelo is None else a_dominio(modelo)

    def listar_por_expediente(self, expediente_id: str) -> list[SeleccionProveedor]:
        with self._session_factory() as session:
            modelos = session.scalars(
                select(SeleccionProveedorModel)
                .where(SeleccionProveedorModel.expediente_id == expediente_id)
                .order_by(
                    SeleccionProveedorModel.fecha_seleccion,
                    SeleccionProveedorModel.id_seleccion,
                )
            ).all()
            return [a_dominio(modelo) for modelo in modelos]

    @staticmethod
    def _traducir_integridad(exc: IntegrityError) -> None:
        diagnostico = getattr(exc.orig, "diag", None)
        nombre_restriccion = getattr(diagnostico, "constraint_name", None)
        if nombre_restriccion == "uq_selecciones_proveedor_expediente_vigente":
            raise SeleccionProveedorVigenteError(
                "El Expediente ya posee una selección vigente."
            ) from exc
