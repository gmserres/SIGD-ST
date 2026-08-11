from dataclasses import asdict

from app.domain.control_proveedor_op import EstadoControlProveedorOP
from app.domain.habilitacion_proveedor_op import (
    EstadoHabilitacionProveedorOP,
    HabilitacionProveedorOP,
)
from app.repositories.control_proveedor_op_repository import (
    ControlProveedorOPRepository,
)
from app.repositories.proveedor_repository import ProveedorRepository
from app.repositories.seleccion_proveedor_repository import (
    SeleccionProveedorRepository,
)
from app.schemas.habilitacion_proveedor_op import HabilitacionProveedorOPRead
from app.services.analisis_op import (
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)
from app.services.documentos import DocumentoService
from app.services.expedientes import ExpedienteService


class EvaluarHabilitacionProveedorOPService:
    def __init__(
        self,
        expediente_service: ExpedienteService,
        documento_service: DocumentoService,
        seleccion_repository: SeleccionProveedorRepository,
        control_repository: ControlProveedorOPRepository,
        proveedor_repository: ProveedorRepository,
    ) -> None:
        self._expedientes = expediente_service
        self._documentos = documento_service
        self._selecciones = seleccion_repository
        self._controles = control_repository
        self._proveedores = proveedor_repository

    def evaluar(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> HabilitacionProveedorOPRead:
        expediente = self._expedientes.obtener(expediente_id)
        self._validar_documento(expediente_id, documento_op_id)
        solicitud_id = expediente.solicitud_intervencion_id

        if solicitud_id is None:
            return self._resultado(
                expediente_id,
                documento_op_id,
                EstadoHabilitacionProveedorOP.SIN_SOLICITUD_ASOCIADA,
                mensaje="El Expediente no posee una Solicitud asociada.",
                proxima_accion=(
                    "Resolver la asociación administrativa con una Solicitud."
                ),
            )

        seleccion = self._selecciones.obtener_vigente_por_solicitud(
            solicitud_id
        )
        if seleccion is None:
            return self._resultado(
                expediente_id,
                documento_op_id,
                EstadoHabilitacionProveedorOP.REQUIERE_SELECCION_PROVEEDOR,
                solicitud_id=solicitud_id,
                mensaje=(
                    "La Solicitud no posee una selección de proveedor vigente."
                ),
                proxima_accion=(
                    "Registrar administrativamente al proveedor identificado "
                    "en la OP y ejecutar un nuevo control."
                ),
            )

        ultimo = self._controles.obtener_ultimo_por_documento(documento_op_id)
        if ultimo is None or not self._corresponde_a_seleccion_vigente(
            ultimo,
            expediente_id=expediente_id,
            documento_op_id=documento_op_id,
            solicitud_id=solicitud_id,
            seleccion_id=seleccion.id_seleccion,
        ):
            return self._resultado(
                expediente_id,
                documento_op_id,
                EstadoHabilitacionProveedorOP.REQUIERE_NUEVO_CONTROL,
                solicitud_id=solicitud_id,
                seleccion_id=seleccion.id_seleccion,
                mensaje=(
                    "No existe un control autoritativo correspondiente a la "
                    "selección actualmente vigente."
                ),
                proxima_accion="Ejecutar un nuevo control contra esta OP.",
            )

        if ultimo.estado == EstadoControlProveedorOP.NO_VERIFICABLE:
            return self._resultado(
                expediente_id,
                documento_op_id,
                EstadoHabilitacionProveedorOP.PROVEEDOR_NO_VERIFICABLE,
                solicitud_id=solicitud_id,
                seleccion_id=seleccion.id_seleccion,
                control_id=ultimo.id_control,
                mensaje=(
                    "La OP no permite identificar confiablemente al proveedor "
                    "definitivo."
                ),
                proxima_accion=(
                    "Corregir o reemplazar la documentación y ejecutar un "
                    "nuevo control."
                ),
            )

        if ultimo.estado == EstadoControlProveedorOP.CUIT_DIFERENTE:
            proveedor = (
                self._proveedores.obtener_por_cuit(ultimo.cuit_detectado)
                if ultimo.cuit_detectado is not None
                else None
            )
            return self._resultado(
                expediente_id,
                documento_op_id,
                EstadoHabilitacionProveedorOP.REQUIERE_REASIGNACION_PROVEEDOR,
                solicitud_id=solicitud_id,
                seleccion_id=seleccion.id_seleccion,
                control_id=ultimo.id_control,
                proveedor_id=(
                    proveedor.id_proveedor if proveedor is not None else None
                ),
                cuit=ultimo.cuit_detectado,
                razon_social=ultimo.razon_social_detectada,
                en_maestro=proveedor is not None,
                activo=proveedor.activo if proveedor is not None else None,
                mensaje=(
                    "El proveedor identificado en la OP difiere del "
                    "seleccionado administrativamente."
                ),
                proxima_accion=(
                    "Confirmar el alta o identificación del proveedor de la "
                    "OP, reemplazar la selección con motivo y ejecutar un "
                    "nuevo control."
                ),
            )

        if ultimo.estado != EstadoControlProveedorOP.COINCIDE:
            raise RuntimeError(
                "El último control posee un estado no contemplado."
            )
        if ultimo.cuit_detectado is None:
            raise RuntimeError(
                "El control COINCIDE no contiene el CUIT documental "
                "obligatorio de la OP."
            )

        return self._resultado(
            expediente_id,
            documento_op_id,
            EstadoHabilitacionProveedorOP.HABILITADO,
            solicitud_id=solicitud_id,
            seleccion_id=seleccion.id_seleccion,
            control_id=ultimo.id_control,
            proveedor_id=seleccion.proveedor_id,
            cuit=ultimo.cuit_detectado,
            razon_social=ultimo.razon_social_detectada,
            mensaje=(
                "El proveedor identificado en la OP coincide con la "
                "selección vigente."
            ),
            proxima_accion=None,
        )

    def _validar_documento(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> None:
        documento = self._documentos.obtener_por_id(documento_op_id)
        if documento is None:
            raise DocumentoOPNoEncontradoError(documento_op_id)
        if documento.expediente_id != expediente_id:
            raise DocumentoOPExpedienteInconsistenteError(
                documento_op_id,
                expediente_id,
            )
        if documento.tipo.upper() != "OP":
            raise DocumentoNoEsOPError(documento_op_id)

    @staticmethod
    def _corresponde_a_seleccion_vigente(
        control,
        *,
        expediente_id: str,
        documento_op_id: str,
        solicitud_id: str,
        seleccion_id: str,
    ) -> bool:
        return (
            control.expediente_id == expediente_id
            and control.documento_op_id == documento_op_id
            and control.solicitud_intervencion_id == solicitud_id
            and control.seleccion_proveedor_id == seleccion_id
        )

    @staticmethod
    def _resultado(
        expediente_id: str,
        documento_op_id: str,
        estado: EstadoHabilitacionProveedorOP,
        *,
        solicitud_id: str | None = None,
        seleccion_id: str | None = None,
        control_id: str | None = None,
        proveedor_id: str | None = None,
        cuit: str | None = None,
        razon_social: str | None = None,
        en_maestro: bool | None = None,
        activo: bool | None = None,
        mensaje: str,
        proxima_accion: str | None,
    ) -> HabilitacionProveedorOPRead:
        resultado = HabilitacionProveedorOP(
            expediente_id=expediente_id,
            documento_op_id=documento_op_id,
            estado=estado,
            solicitud_intervencion_id=solicitud_id,
            seleccion_proveedor_id=seleccion_id,
            control_proveedor_op_id=control_id,
            proveedor_definitivo_id=proveedor_id,
            proveedor_definitivo_cuit=cuit,
            proveedor_definitivo_razon_social=razon_social,
            proveedor_op_en_maestro=en_maestro,
            proveedor_op_activo=activo,
            mensaje=mensaje,
            proxima_accion=proxima_accion,
        )
        return HabilitacionProveedorOPRead(**asdict(resultado))
