from dataclasses import asdict
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.decision_administrativa import DecisionAdministrativa
from app.domain.proveedor import Proveedor
from app.domain.seleccion_proveedor import (
    DecisionNoAprobatoriaError,
    DecisionSeleccionInexistenteError,
    DecisionSolicitudInconsistenteError,
    ExpedienteSeleccionIncompletoError,
    ExpedienteSeleccionInexistenteError,
    FondoSeleccionIncompatibleError,
    MismoProveedorSeleccionadoError,
    ProveedorInactivoError,
    ProveedorSeleccionInexistenteError,
    SeleccionProveedor,
    SeleccionProveedorInexistenteError,
    SeleccionProveedorVigenteError,
    SolicitudSeleccionInexistenteError,
)
from app.repositories.decision_administrativa_repository import DecisionAdministrativaRepository
from app.repositories.expediente_repository import ExpedienteRepository
from app.repositories.proveedor_repository import ProveedorRepository
from app.repositories.seleccion_proveedor_repository import SeleccionProveedorRepository
from app.repositories.solicitud_intervencion_repository import SolicitudIntervencionRepository
from app.schemas.seleccion_proveedor import ReemplazoProveedorCreate, SeleccionProveedorCreate, SeleccionProveedorRead


class SeleccionProveedorService:
    def __init__(
        self,
        expediente_repository: ExpedienteRepository,
        solicitud_repository: SolicitudIntervencionRepository,
        decision_repository: DecisionAdministrativaRepository,
        proveedor_repository: ProveedorRepository,
        seleccion_repository: SeleccionProveedorRepository,
    ) -> None:
        self._expedientes = expediente_repository
        self._solicitudes = solicitud_repository
        self._decisiones = decision_repository
        self._proveedores = proveedor_repository
        self._selecciones = seleccion_repository

    def seleccionar(self, expediente_id: str, data: SeleccionProveedorCreate) -> SeleccionProveedorRead:
        expediente, solicitud, decision = self._obtener_contexto(expediente_id)
        if self._selecciones.obtener_vigente_por_expediente(expediente_id) is not None:
            raise SeleccionProveedorVigenteError(
                "El Expediente ya posee una selección vigente."
            )
        proveedor = self._obtener_proveedor_activo(data.proveedor_id)
        seleccion = self._crear_seleccion(
            expediente_id=expediente.id,
            solicitud_id=solicitud.id_solicitud,
            decision=decision,
            proveedor=proveedor,
            seleccionado_por=data.seleccionado_por,
            motivo_reemplazo=None,
        )
        self._selecciones.guardar(seleccion)
        return self._a_read(seleccion)

    def reemplazar(self, expediente_id: str, data: ReemplazoProveedorCreate) -> SeleccionProveedorRead:
        expediente, solicitud, decision = self._obtener_contexto(expediente_id)
        seleccion_vigente = self._selecciones.obtener_vigente_por_expediente(expediente_id)
        if seleccion_vigente is None:
            raise SeleccionProveedorInexistenteError(
                "El Expediente no posee una selección vigente."
            )
        motivo_reemplazo = data.motivo_reemplazo.strip()
        if not motivo_reemplazo:
            raise ValueError("El motivo del reemplazo es obligatorio.")
        if seleccion_vigente.proveedor_id == data.proveedor_id:
            raise MismoProveedorSeleccionadoError(
                "El nuevo Proveedor debe ser diferente del vigente."
            )
        proveedor = self._obtener_proveedor_activo(data.proveedor_id)
        nueva_seleccion = self._crear_seleccion(
            expediente_id=expediente.id,
            solicitud_id=solicitud.id_solicitud,
            decision=decision,
            proveedor=proveedor,
            seleccionado_por=data.seleccionado_por,
            motivo_reemplazo=motivo_reemplazo,
            fecha_seleccion=self._fecha_reemplazo(
                seleccion_vigente.fecha_seleccion
            ),
        )
        self._selecciones.reemplazar(seleccion_vigente, nueva_seleccion)
        return self._a_read(nueva_seleccion)

    def obtener_vigente(self, expediente_id: str) -> SeleccionProveedorRead:
        self._obtener_contexto(expediente_id)
        seleccion = self._selecciones.obtener_vigente_por_expediente(expediente_id)
        if seleccion is None:
            raise SeleccionProveedorInexistenteError(
                "El Expediente no posee una selección vigente."
            )
        return self._a_read(seleccion)

    def listar_historial(self, expediente_id: str) -> list[SeleccionProveedorRead]:
        self._obtener_contexto(expediente_id)
        return [
            self._a_read(seleccion)
            for seleccion in self._selecciones.listar_por_expediente(expediente_id)
        ]

    def _obtener_solicitud(self, solicitud_id: str):
        solicitud = self._solicitudes.obtener_por_id(solicitud_id)
        if solicitud is None:
            raise SolicitudSeleccionInexistenteError(
                "Solicitud de Intervención no encontrada."
            )
        return solicitud

    def _obtener_contexto(self, expediente_id: str):
        expediente = self._expedientes.obtener_por_id(expediente_id)
        if expediente is None:
            raise ExpedienteSeleccionInexistenteError("Expediente no encontrado.")
        solicitud_id = expediente.solicitud_intervencion_id
        decision_id = expediente.decision_administrativa_id
        if solicitud_id is None or decision_id is None:
            raise ExpedienteSeleccionIncompletoError(
                "El Expediente no posee Solicitud y Decisión asociadas."
            )
        solicitud = self._obtener_solicitud(solicitud_id)
        decision = self._decisiones.obtener_por_id(decision_id)
        if decision is None:
            raise DecisionSeleccionInexistenteError(
                "Decisión administrativa no encontrada."
            )
        if decision.solicitud_intervencion_id != solicitud_id:
            raise DecisionSolicitudInconsistenteError(
                "La Decisión no corresponde a la Solicitud."
            )
        if not decision.aprueba_intervencion:
            raise DecisionNoAprobatoriaError(
                "La Decisión asociada no aprueba la intervención."
            )
        if decision.fondo_interviniente != "FONDO_COMPENSADOR":
            raise FondoSeleccionIncompatibleError(
                "El Fondo Interviniente no corresponde al circuito habilitado."
            )
        return expediente, solicitud, decision

    def _obtener_proveedor_activo(self, proveedor_id: str) -> Proveedor:
        proveedor = self._proveedores.obtener_por_id(proveedor_id)
        if proveedor is None:
            raise ProveedorSeleccionInexistenteError("Proveedor no encontrado.")
        if not proveedor.activo:
            raise ProveedorInactivoError(
                "No puede seleccionarse un Proveedor inactivo."
            )
        return proveedor

    @staticmethod
    def _crear_seleccion(
        *,
        expediente_id: str,
        solicitud_id: str,
        decision: DecisionAdministrativa,
        proveedor: Proveedor,
        seleccionado_por: str,
        motivo_reemplazo: str | None,
        fecha_seleccion: datetime | None = None,
    ) -> SeleccionProveedor:
        return SeleccionProveedor(
            id_seleccion=str(uuid4()),
            expediente_id=expediente_id,
            solicitud_intervencion_id=solicitud_id,
            decision_administrativa_id=decision.id_decision,
            proveedor_id=proveedor.id_proveedor,
            fecha_seleccion=fecha_seleccion or datetime.now(),
            seleccionado_por=seleccionado_por,
            proveedor_cuit=proveedor.cuit,
            proveedor_razon_social=proveedor.razon_social,
            motivo_reemplazo=motivo_reemplazo,
            vigente=True,
        )

    @staticmethod
    def _fecha_reemplazo(
        fecha_anterior: datetime,
    ) -> datetime:
        ahora = datetime.now()
        if ahora > fecha_anterior:
            return ahora
        return fecha_anterior + timedelta(microseconds=1)

    @staticmethod
    def _a_read(seleccion: SeleccionProveedor) -> SeleccionProveedorRead:
        return SeleccionProveedorRead(**asdict(seleccion))
