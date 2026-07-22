from datetime import datetime
from dataclasses import replace

from app.domain.estados import EstadoExpediente
from app.domain.expediente import Expediente
from app.repositories.expediente_repository import ExpedienteRepository
from app.schemas.expediente import ExpedienteCreate, ExpedienteRead, ExpedienteUpdate

class ExpedienteService:
    def __init__(self, repository: ExpedienteRepository) -> None:
        self._repository = repository

    def crear(self, data: ExpedienteCreate) -> ExpedienteRead:
        expediente = Expediente(
            id=self._repository.siguiente_id(),
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
        self._repository.guardar(expediente)
        return self._a_read(expediente)

    def listar(self) -> list[ExpedienteRead]:
        return [self._a_read(expediente) for expediente in self._repository.listar()]

    def obtener(self, expediente_id: str) -> ExpedienteRead:
        expediente = self._repository.obtener_por_id(expediente_id)
        if expediente is None:
            raise KeyError(expediente_id)
        return self._a_read(expediente)

    def actualizar(self, expediente_id: str, data: ExpedienteUpdate) -> ExpedienteRead:
        expediente = self._obtener_dominio(expediente_id)
        actualizado = replace(expediente, **data.model_dump(exclude_unset=True))
        self._repository.guardar(actualizado)
        return self._a_read(actualizado)

    def cambiar_estado(self, expediente_id: str, estado: EstadoExpediente) -> ExpedienteRead:
        expediente = self._obtener_dominio(expediente_id)
        actualizado = replace(expediente, estado=estado)
        self._repository.guardar(actualizado)
        return self._a_read(actualizado)

    def _obtener_dominio(self, expediente_id: str) -> Expediente:
        expediente = self._repository.obtener_por_id(expediente_id)
        if expediente is None:
            raise KeyError(expediente_id)
        return expediente

    @staticmethod
    def _a_read(expediente: Expediente) -> ExpedienteRead:
        return ExpedienteRead(**expediente.__dict__)
