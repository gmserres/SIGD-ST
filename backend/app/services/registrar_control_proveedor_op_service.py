from collections.abc import Callable
from datetime import datetime
from uuid import uuid4

from app.domain.control_proveedor_op import EstadoControlProveedorOP
from app.domain.control_proveedor_op_evidencia import (
    ControlProveedorOPEvidencia,
)
from app.repositories.control_proveedor_op_repository import (
    ControlProveedorOPRepository,
)
from app.schemas.control_proveedor_op import (
    ControlProveedorOPRead,
    EstadoControlProveedorOPAdministrativo,
)
from app.schemas.control_proveedor_op_registro import (
    ControlProveedorOPRegistroRead,
)
from app.services.control_proveedor_op_service import (
    ControlProveedorOPService,
)


ESTADOS_PERSISTIBLES = frozenset(
    {
        EstadoControlProveedorOPAdministrativo.COINCIDE,
        EstadoControlProveedorOPAdministrativo.CUIT_DIFERENTE,
        EstadoControlProveedorOPAdministrativo.NO_VERIFICABLE,
    }
)


def generar_id_control() -> str:
    return str(uuid4())


class RegistrarControlProveedorOPService:
    def __init__(
        self,
        control_service: ControlProveedorOPService,
        repository: ControlProveedorOPRepository,
        *,
        ahora: Callable[[], datetime] = datetime.now,
        generar_id: Callable[[], str] = generar_id_control,
    ) -> None:
        self._control_service = control_service
        self._repository = repository
        self._ahora = ahora
        self._generar_id = generar_id

    def ejecutar(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> ControlProveedorOPRegistroRead:
        resultado = self._control_service.ejecutar(
            expediente_id,
            documento_op_id,
        )
        if resultado.estado not in ESTADOS_PERSISTIBLES:
            return self._sin_persistencia(resultado)

        self._validar_resultado_persistible(resultado)
        control = ControlProveedorOPEvidencia(
            id_control=self._generar_id(),
            expediente_id=resultado.expediente_id,
            documento_op_id=resultado.documento_op_id,
            solicitud_intervencion_id=(
                resultado.solicitud_intervencion_id
            ),
            seleccion_proveedor_id=resultado.seleccion_proveedor_id,
            estado=EstadoControlProveedorOP(resultado.estado.value),
            proveedor_cuit_seleccionado=resultado.cuit_seleccionado,
            proveedor_razon_social_seleccionada=(
                resultado.razon_social_seleccionada
            ),
            cuit_detectado=resultado.cuit_detectado,
            razon_social_detectada=resultado.razon_social_detectada,
            advertencias=tuple(resultado.advertencias),
            fecha_control=self._ahora(),
            modo_analisis=resultado.modo_analisis,
        )
        guardado = self._repository.guardar(control)
        return self._desde_evidencia(guardado)

    @staticmethod
    def _validar_resultado_persistible(
        resultado: ControlProveedorOPRead,
    ) -> None:
        requeridos = (
            resultado.solicitud_intervencion_id,
            resultado.seleccion_proveedor_id,
            resultado.cuit_seleccionado,
            resultado.razon_social_seleccionada,
            resultado.modo_analisis,
        )
        if any(valor is None for valor in requeridos):
            raise RuntimeError(
                "El resultado persistible del control está incompleto."
            )

    @staticmethod
    def _sin_persistencia(
        resultado: ControlProveedorOPRead,
    ) -> ControlProveedorOPRegistroRead:
        return ControlProveedorOPRegistroRead(
            **resultado.model_dump(),
            id_control=None,
            fecha_control=None,
        )

    @staticmethod
    def _desde_evidencia(
        control: ControlProveedorOPEvidencia,
    ) -> ControlProveedorOPRegistroRead:
        return ControlProveedorOPRegistroRead(
            id_control=control.id_control,
            fecha_control=control.fecha_control,
            expediente_id=control.expediente_id,
            documento_op_id=control.documento_op_id,
            solicitud_intervencion_id=control.solicitud_intervencion_id,
            seleccion_proveedor_id=control.seleccion_proveedor_id,
            estado=EstadoControlProveedorOPAdministrativo(
                control.estado.value
            ),
            cuit_seleccionado=control.proveedor_cuit_seleccionado,
            cuit_detectado=control.cuit_detectado,
            razon_social_seleccionada=(
                control.proveedor_razon_social_seleccionada
            ),
            razon_social_detectada=control.razon_social_detectada,
            advertencias=list(control.advertencias),
            modo_analisis=control.modo_analisis,
        )
