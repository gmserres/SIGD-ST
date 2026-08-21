from dataclasses import dataclass
from typing import Protocol

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


@dataclass(frozen=True)
class FuentesTimelineExpediente:
    expediente: ExpedienteModel
    documentos: list[DocumentoModel]
    checklist: ChecklistFisicoModel | None
    validaciones: list[ValidacionAdministrativaModel]
    selecciones: list[SeleccionProveedorModel]
    controles: list[ControlProveedorOPModel]
    disposiciones: list[DisposicionModel]


class TimelineExpedienteRepository(Protocol):
    def obtener_fuentes(
        self,
        expediente_id: str,
    ) -> FuentesTimelineExpediente | None: ...
