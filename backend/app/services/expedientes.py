from datetime import datetime
from uuid import uuid4

from app.domain.estados import EstadoExpediente
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead, ExpedienteUpdate

class ExpedienteService:
    def __init__(self) -> None:
        self._expedientes: dict[str, ExpedienteRead] = {}

    def crear(self, data: ExpedienteCreate) -> ExpedienteRead:
        expediente_id = f"EXP-{len(self._expedientes) + 1:06d}"
        expediente = ExpedienteRead(
            id=expediente_id,
            numero_interno=data.numero_interno,
            numero_gdeba=data.numero_gdeba,
            solicitud_intervencion_id=data.solicitud_intervencion_id,
            decision_administrativa_id=data.decision_administrativa_id,
            id_suna=data.id_suna,
            tipo_tramite=data.tipo_tramite,
            estado=EstadoExpediente.BORRADOR,
            establecimiento=data.establecimiento,
            objeto=data.objeto,
            numero_disposicion=data.numero_disposicion,
            creado=datetime.now(),
        )
        self._expedientes[expediente_id] = expediente
        return expediente

    def listar(self) -> list[ExpedienteRead]:
        return list(self._expedientes.values())

    def obtener(self, expediente_id: str) -> ExpedienteRead:
        return self._expedientes[expediente_id]

    def actualizar(self, expediente_id: str, data: ExpedienteUpdate) -> ExpedienteRead:
        expediente = self._expedientes[expediente_id]
        actualizado = expediente.model_copy(
            update=data.model_dump(exclude_unset=True)
        )
        self._expedientes[expediente_id] = actualizado
        return actualizado

    def cambiar_estado(self, expediente_id: str, estado: EstadoExpediente) -> ExpedienteRead:
        expediente = self._expedientes[expediente_id]
        actualizado = expediente.model_copy(update={"estado": estado})
        self._expedientes[expediente_id] = actualizado
        return actualizado


expediente_service = ExpedienteService()
