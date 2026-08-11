from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.seleccion_proveedor import SeleccionProveedor, SeleccionProveedorVigenteError
from app.infrastructure.database.mappers.seleccion_proveedor_mapper import a_dominio, a_modelo
from app.infrastructure.database.models.seleccion_proveedor_model import SeleccionProveedorModel


class PostgresSeleccionProveedorRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def guardar(self, seleccion: SeleccionProveedor) -> None:
        with self._session_factory() as session:
            try:
                session.add(a_modelo(seleccion))
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                self._traducir_integridad(exc)
                raise

    def reemplazar(self, anterior: SeleccionProveedor, nueva: SeleccionProveedor) -> None:
        with self._session_factory() as session:
            try:
                modelo_anterior = session.get(SeleccionProveedorModel, anterior.id_seleccion)
                if (
                    modelo_anterior is None
                    or not modelo_anterior.vigente
                    or modelo_anterior.solicitud_intervencion_id
                    != anterior.solicitud_intervencion_id
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

    def obtener_vigente_por_solicitud(self, solicitud_id: str) -> SeleccionProveedor | None:
        with self._session_factory() as session:
            modelo = session.scalar(
                select(SeleccionProveedorModel).where(
                    SeleccionProveedorModel.solicitud_intervencion_id == solicitud_id,
                    SeleccionProveedorModel.vigente.is_(True),
                )
            )
            return None if modelo is None else a_dominio(modelo)

    def listar_por_solicitud(self, solicitud_id: str) -> list[SeleccionProveedor]:
        with self._session_factory() as session:
            modelos = session.scalars(
                select(SeleccionProveedorModel)
                .where(SeleccionProveedorModel.solicitud_intervencion_id == solicitud_id)
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
        if nombre_restriccion == "uq_selecciones_proveedor_solicitud_vigente":
            raise SeleccionProveedorVigenteError(
                "La Solicitud ya posee una selección vigente."
            ) from exc
