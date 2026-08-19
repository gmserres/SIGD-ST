from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.control_proveedor_op_evidencia import (
    ControlProveedorOPEvidencia,
)
from app.infrastructure.database.mappers.control_proveedor_op_mapper import (
    a_dominio,
    a_modelo,
    documento_id_a_secuencia,
)
from app.infrastructure.database.models.control_proveedor_op_model import (
    ControlProveedorOPModel,
)
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.seleccion_proveedor_model import (
    SeleccionProveedorModel,
)
from app.repositories.control_proveedor_op_repository import (
    SeleccionControlObsoletaError,
)
from app.infrastructure.database.persistence.mutabilidad_expediente import (
    bloquear_expediente_mutable,
)


class PostgresControlProveedorOPRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._session_factory = session_factory

    def guardar(
        self,
        control: ControlProveedorOPEvidencia,
    ) -> ControlProveedorOPEvidencia:
        with self._session_factory() as session:
            try:
                bloquear_expediente_mutable(session, control.expediente_id)
                seleccion = session.scalar(
                    select(SeleccionProveedorModel)
                    .where(
                        SeleccionProveedorModel.id_seleccion
                        == control.seleccion_proveedor_id
                    )
                    .with_for_update()
                )
                if (
                    seleccion is None
                    or not seleccion.vigente
                    or seleccion.expediente_id != control.expediente_id
                    or str(seleccion.solicitud_intervencion_id)
                    != control.solicitud_intervencion_id
                    or seleccion.proveedor_cuit
                    != control.proveedor_cuit_seleccionado
                    or seleccion.proveedor_razon_social
                    != control.proveedor_razon_social_seleccionada
                ):
                    raise SeleccionControlObsoletaError()

                documento = session.get(
                    DocumentoModel,
                    documento_id_a_secuencia(control.documento_op_id),
                )
                if (
                    documento is None
                    or documento.expediente_id != control.expediente_id
                    or documento.tipo.upper() != "OP"
                ):
                    raise ValueError(
                        "El Documento OP no corresponde al Expediente."
                    )
                modelo = a_modelo(control)
                self._preparar_secuencia_sqlite(session, modelo)
                session.add(modelo)
                session.flush()
                guardado = a_dominio(modelo)
                session.commit()
                return guardado
            except Exception:
                session.rollback()
                raise

    def obtener_por_id(
        self,
        id_control: str,
    ) -> ControlProveedorOPEvidencia | None:
        with self._session_factory() as session:
            modelo = session.get(ControlProveedorOPModel, id_control)
            return a_dominio(modelo) if modelo is not None else None

    def listar_por_documento(
        self,
        documento_op_id: str,
    ) -> list[ControlProveedorOPEvidencia]:
        secuencia = documento_id_a_secuencia(documento_op_id)
        with self._session_factory() as session:
            modelos = session.scalars(
                select(ControlProveedorOPModel)
                .where(
                    ControlProveedorOPModel.documento_secuencia
                    == secuencia
                )
                .order_by(ControlProveedorOPModel.secuencia)
            ).all()
            return [a_dominio(modelo) for modelo in modelos]

    def obtener_ultimo_por_documento(
        self,
        documento_op_id: str,
    ) -> ControlProveedorOPEvidencia | None:
        secuencia = documento_id_a_secuencia(documento_op_id)
        with self._session_factory() as session:
            modelo = session.scalar(
                select(ControlProveedorOPModel)
                .where(
                    ControlProveedorOPModel.documento_secuencia
                    == secuencia
                )
                .order_by(ControlProveedorOPModel.secuencia.desc())
                .limit(1)
            )
            return a_dominio(modelo) if modelo is not None else None

    @staticmethod
    def _preparar_secuencia_sqlite(
        session: Session,
        modelo: ControlProveedorOPModel,
    ) -> None:
        if session.get_bind().dialect.name != "sqlite":
            return
        ultima_secuencia = session.scalar(
            select(func.max(ControlProveedorOPModel.secuencia))
        )
        modelo.secuencia = (ultima_secuencia or 0) + 1
