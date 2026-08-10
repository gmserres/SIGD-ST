from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.proveedor import (
    CuitProveedorDuplicadoError,
    Proveedor,
    normalizar_cuit,
)
from app.infrastructure.database.mappers.proveedor_mapper import (
    a_dominio,
    a_modelo,
    actualizar_modelo,
)
from app.infrastructure.database.models.proveedor_model import (
    ProveedorModel,
)


class PostgresProveedorRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(self, proveedor: Proveedor) -> None:
        with self._session_factory() as session:
            try:
                modelo = session.get(
                    ProveedorModel,
                    proveedor.id_proveedor,
                )
                if modelo is None:
                    session.add(a_modelo(proveedor))
                else:
                    actualizar_modelo(modelo, proveedor)
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                diagnostico = getattr(exc.orig, "diag", None)
                constraint_name = getattr(
                    diagnostico,
                    "constraint_name",
                    None,
                )
                if constraint_name == "uq_proveedores_cuit":
                    raise CuitProveedorDuplicadoError(
                        "Ya existe un proveedor registrado con ese CUIT."
                    ) from exc
                raise
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(
        self,
        proveedor_id: str,
    ) -> Proveedor | None:
        with self._session_factory() as session:
            modelo = session.get(ProveedorModel, proveedor_id)
            if modelo is None:
                return None
            return a_dominio(modelo)

    def obtener_por_cuit(
        self,
        cuit: str,
    ) -> Proveedor | None:
        cuit_normalizado = normalizar_cuit(cuit)
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ProveedorModel).where(
                    ProveedorModel.cuit == cuit_normalizado
                )
            )
            if modelo is None:
                return None
            return a_dominio(modelo)

    def listar(
        self,
        *,
        buscar: str | None = None,
        activo: bool | None = None,
    ) -> list[Proveedor]:
        with self._session_factory() as session:
            consulta = select(ProveedorModel)

            if buscar is not None and buscar.strip():
                termino = buscar.strip()
                try:
                    cuit = normalizar_cuit(termino)
                except (TypeError, ValueError):
                    cuit = None

                condiciones = [
                    ProveedorModel.razon_social.icontains(
                        termino,
                        autoescape=True,
                    )
                ]
                if cuit is not None:
                    condiciones.append(ProveedorModel.cuit == cuit)
                consulta = consulta.where(or_(*condiciones))

            if activo is not None:
                consulta = consulta.where(
                    ProveedorModel.activo.is_(activo)
                )

            consulta = consulta.order_by(
                ProveedorModel.razon_social,
                ProveedorModel.cuit,
                ProveedorModel.id_proveedor,
            )
            modelos = session.scalars(consulta).all()
            return [a_dominio(modelo) for modelo in modelos]
