from dataclasses import asdict
from datetime import datetime
from uuid import uuid4

from app.domain.decision_administrativa import DecisionAdministrativa
from app.domain.proveedor import Proveedor
from app.domain.seleccion_proveedor import (
    DecisionNoAprobatoriaError,
    DecisionSeleccionInexistenteError,
    DecisionSolicitudInconsistenteError,
    MismoProveedorSeleccionadoError,
    ProveedorInactivoError,
    ProveedorSeleccionInexistenteError,
    SeleccionProveedor,
    SeleccionProveedorInexistenteError,
    SeleccionProveedorVigenteError,
    SolicitudSeleccionInexistenteError,
)
from app.repositories.decision_administrativa_repository import DecisionAdministrativaRepository
from app.repositories.proveedor_repository import ProveedorRepository
from app.repositories.seleccion_proveedor_repository import SeleccionProveedorRepository
from app.repositories.solicitud_intervencion_repository import SolicitudIntervencionRepository
from app.schemas.seleccion_proveedor import ReemplazoProveedorCreate, SeleccionProveedorCreate, SeleccionProveedorRead


class SeleccionProveedorService:
    def __init__(
        self,
        solicitud_repository: SolicitudIntervencionRepository,
        decision_repository: DecisionAdministrativaRepository,
        proveedor_repository: ProveedorRepository,
        seleccion_repository: SeleccionProveedorRepository,
    ) -> None:
        self._solicitudes = solicitud_repository
        self._decisiones = decision_repository
        self._proveedores = proveedor_repository
        self._selecciones = seleccion_repository

    def seleccionar(self, solicitud_id: str, data: SeleccionProveedorCreate) -> SeleccionProveedorRead:
        decision = self._obtener_decision_aprobatoria(solicitud_id)
        if self._selecciones.obtener_vigente_por_solicitud(solicitud_id) is not None:
            raise SeleccionProveedorVigenteError(
                "La Solicitud ya posee una selección vigente."
            )
        proveedor = self._obtener_proveedor_activo(data.proveedor_id)
        seleccion = self._crear_seleccion(
            solicitud_id=solicitud_id,
            decision=decision,
            proveedor=proveedor,
            seleccionado_por=data.seleccionado_por,
            motivo_reemplazo=None,
        )
        self._selecciones.guardar(seleccion)
        return self._a_read(seleccion)

    def reemplazar(self, solicitud_id: str, data: ReemplazoProveedorCreate) -> SeleccionProveedorRead:
        decision = self._obtener_decision_aprobatoria(solicitud_id)
        seleccion_vigente = self._selecciones.obtener_vigente_por_solicitud(solicitud_id)
        if seleccion_vigente is None:
            raise SeleccionProveedorInexistenteError(
                "La Solicitud no posee una selección vigente."
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
            solicitud_id=solicitud_id,
            decision=decision,
            proveedor=proveedor,
            seleccionado_por=data.seleccionado_por,
            motivo_reemplazo=motivo_reemplazo,
        )
        self._selecciones.reemplazar(seleccion_vigente, nueva_seleccion)
        return self._a_read(nueva_seleccion)

    def obtener_vigente(self, solicitud_id: str) -> SeleccionProveedorRead:
        self._obtener_solicitud(solicitud_id)
        seleccion = self._selecciones.obtener_vigente_por_solicitud(solicitud_id)
        if seleccion is None:
            raise SeleccionProveedorInexistenteError(
                "La Solicitud no posee una selección vigente."
            )
        return self._a_read(seleccion)

    def listar_historial(self, solicitud_id: str) -> list[SeleccionProveedorRead]:
        self._obtener_solicitud(solicitud_id)
        return [
            self._a_read(seleccion)
            for seleccion in self._selecciones.listar_por_solicitud(solicitud_id)
        ]

    def _obtener_solicitud(self, solicitud_id: str):
        solicitud = self._solicitudes.obtener_por_id(solicitud_id)
        if solicitud is None:
            raise SolicitudSeleccionInexistenteError(
                "Solicitud de Intervención no encontrada."
            )
        return solicitud

    def _obtener_decision_aprobatoria(self, solicitud_id: str) -> DecisionAdministrativa:
        self._obtener_solicitud(solicitud_id)
        decisiones = self._decisiones.listar(
            solicitud_intervencion_id=solicitud_id
        )
        if not decisiones:
            raise DecisionSeleccionInexistenteError(
                "La Solicitud no posee una Decisión registrada."
            )
        decision_actual = decisiones[-1]
        if decision_actual.solicitud_intervencion_id != solicitud_id:
            raise DecisionSolicitudInconsistenteError(
                "La Decisión no corresponde a la Solicitud."
            )
        if not decision_actual.aprueba_intervencion:
            raise DecisionNoAprobatoriaError(
                "La última Decisión no aprueba la intervención."
            )
        return decision_actual

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
        solicitud_id: str,
        decision: DecisionAdministrativa,
        proveedor: Proveedor,
        seleccionado_por: str,
        motivo_reemplazo: str | None,
    ) -> SeleccionProveedor:
        return SeleccionProveedor(
            id_seleccion=str(uuid4()),
            solicitud_intervencion_id=solicitud_id,
            decision_administrativa_id=decision.id_decision,
            proveedor_id=proveedor.id_proveedor,
            fecha_seleccion=datetime.now(),
            seleccionado_por=seleccionado_por,
            proveedor_cuit=proveedor.cuit,
            proveedor_razon_social=proveedor.razon_social,
            motivo_reemplazo=motivo_reemplazo,
            vigente=True,
        )

    @staticmethod
    def _a_read(seleccion: SeleccionProveedor) -> SeleccionProveedorRead:
        return SeleccionProveedorRead(**asdict(seleccion))
