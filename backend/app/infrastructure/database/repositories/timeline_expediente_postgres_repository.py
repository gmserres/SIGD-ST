from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.infrastructure.database.models.checklist_fisico_model import (
    ChecklistFisicoModel,
)
from app.infrastructure.database.models.control_proveedor_op_model import (
    ControlProveedorOPModel,
)
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.infrastructure.database.models.documento_model import DocumentoModel
from app.infrastructure.database.models.expediente_model import ExpedienteModel
from app.infrastructure.database.models.seleccion_proveedor_model import (
    SeleccionProveedorModel,
)
from app.infrastructure.database.models.validacion_administrativa_model import (
    ValidacionAdministrativaModel,
)
from app.repositories.timeline_expediente_repository import (
    FuentesTimelineExpediente,
)


class PostgresTimelineExpedienteRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def obtener_fuentes(
        self,
        expediente_id: str,
    ) -> FuentesTimelineExpediente | None:
        with self._session_factory() as session:
            expediente = session.scalar(
                select(ExpedienteModel).where(
                    ExpedienteModel.id == expediente_id
                )
            )
            if expediente is None:
                return None

            documentos = list(
                session.scalars(
                    select(DocumentoModel)
                    .where(DocumentoModel.expediente_id == expediente_id)
                    .order_by(
                        DocumentoModel.fecha_carga,
                        DocumentoModel.secuencia,
                    )
                ).all()
            )
            checklist = session.scalar(
                select(ChecklistFisicoModel).where(
                    ChecklistFisicoModel.expediente_id == expediente_id
                )
            )
            validaciones = list(
                session.scalars(
                    select(ValidacionAdministrativaModel)
                    .options(
                        selectinload(
                            ValidacionAdministrativaModel.controles
                        )
                    )
                    .where(
                        ValidacionAdministrativaModel.expediente_id
                        == expediente_id
                    )
                    .order_by(
                        ValidacionAdministrativaModel.fecha_validacion,
                        ValidacionAdministrativaModel.id,
                    )
                ).all()
            )
            selecciones = list(
                session.scalars(
                    select(SeleccionProveedorModel)
                    .where(
                        SeleccionProveedorModel.expediente_id
                        == expediente_id
                    )
                    .order_by(
                        SeleccionProveedorModel.fecha_seleccion,
                        SeleccionProveedorModel.id_seleccion,
                    )
                ).all()
            )
            controles = list(
                session.scalars(
                    select(ControlProveedorOPModel)
                    .where(
                        ControlProveedorOPModel.expediente_id
                        == expediente_id
                    )
                    .order_by(
                        ControlProveedorOPModel.fecha_control,
                        ControlProveedorOPModel.secuencia,
                    )
                ).all()
            )
            disposiciones = list(
                session.scalars(
                    select(DisposicionModel)
                    .where(DisposicionModel.expediente_id == expediente_id)
                    .order_by(
                        DisposicionModel.fecha_emision,
                        DisposicionModel.numero_disposicion,
                    )
                ).all()
            )
            session.expunge_all()
            return FuentesTimelineExpediente(
                expediente=expediente,
                documentos=documentos,
                checklist=checklist,
                validaciones=validaciones,
                selecciones=selecciones,
                controles=controles,
                disposiciones=disposiciones,
            )
