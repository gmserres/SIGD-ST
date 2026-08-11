from collections.abc import Callable

from app.domain.control_proveedor_op import (
    ControlProveedorOPResultado,
    comparar_proveedor_op,
)
from app.repositories.seleccion_proveedor_repository import (
    SeleccionProveedorRepository,
)
from app.schemas.control_proveedor_op import (
    ControlProveedorOPRead,
    EstadoControlProveedorOPAdministrativo,
)
from app.services.analisis_op import (
    AnalisisOPService,
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)
from app.services.documentos import DocumentoService
from app.services.expedientes import ExpedienteService


ComparadorProveedorOP = Callable[
    ...,
    ControlProveedorOPResultado,
]


class AnalisisOPDocumentoInconsistenteError(RuntimeError):
    def __init__(
        self,
        documento_op_id: str,
        documento_analizado_id: str | None,
    ) -> None:
        self.documento_op_id = documento_op_id
        self.documento_analizado_id = documento_analizado_id
        super().__init__(
            "El análisis de OP no corresponde al Documento solicitado."
        )


class ControlProveedorOPService:
    def __init__(
        self,
        expediente_service: ExpedienteService,
        documento_service: DocumentoService,
        seleccion_proveedor_repository: (
            SeleccionProveedorRepository
        ),
        analisis_op_service: AnalisisOPService,
        comparador: ComparadorProveedorOP = comparar_proveedor_op,
    ) -> None:
        self._expediente_service = expediente_service
        self._documento_service = documento_service
        self._seleccion_proveedor_repository = (
            seleccion_proveedor_repository
        )
        self._analisis_op_service = analisis_op_service
        self._comparador = comparador

    def ejecutar(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> ControlProveedorOPRead:
        return self._controlar(
            expediente_id,
            documento_op_id,
            reconstruir=False,
        )

    def consultar(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> ControlProveedorOPRead:
        return self._controlar(
            expediente_id,
            documento_op_id,
            reconstruir=True,
        )

    def _controlar(
        self,
        expediente_id: str,
        documento_op_id: str,
        *,
        reconstruir: bool,
    ) -> ControlProveedorOPRead:
        expediente = self._expediente_service.obtener(
            expediente_id
        )
        self._validar_documento_op(
            expediente_id,
            documento_op_id,
        )

        solicitud_id = expediente.solicitud_intervencion_id
        if solicitud_id is None:
            return self._resultado_sin_trazabilidad(
                expediente_id=expediente_id,
                documento_op_id=documento_op_id,
                solicitud_id=None,
                estado=(
                    EstadoControlProveedorOPAdministrativo
                    .SIN_SOLICITUD_ASOCIADA
                ),
            )

        seleccion = (
            self._seleccion_proveedor_repository
            .obtener_vigente_por_solicitud(solicitud_id)
        )
        if seleccion is None:
            return self._resultado_sin_trazabilidad(
                expediente_id=expediente_id,
                documento_op_id=documento_op_id,
                solicitud_id=solicitud_id,
                estado=(
                    EstadoControlProveedorOPAdministrativo
                    .SIN_PROVEEDOR_SELECCIONADO
                ),
            )

        if reconstruir:
            analisis = (
                self._analisis_op_service.reconstruir_documento(
                    expediente_id,
                    documento_op_id,
                )
            )
        else:
            analisis = (
                self._analisis_op_service.analizar_documento(
                    expediente_id,
                    documento_op_id,
                )
            )

        if analisis.documento_op_id != documento_op_id:
            raise AnalisisOPDocumentoInconsistenteError(
                documento_op_id,
                analisis.documento_op_id,
            )

        comparacion = self._comparador(
            proveedor_cuit=seleccion.proveedor_cuit,
            proveedor_razon_social=(
                seleccion.proveedor_razon_social
            ),
            cuit_detectado=analisis.cuit,
            razon_social_detectada=analisis.proveedor,
        )
        return ControlProveedorOPRead(
            expediente_id=expediente_id,
            documento_op_id=documento_op_id,
            solicitud_intervencion_id=solicitud_id,
            seleccion_proveedor_id=seleccion.id_seleccion,
            estado=EstadoControlProveedorOPAdministrativo(
                comparacion.estado.value
            ),
            cuit_seleccionado=comparacion.cuit_seleccionado,
            cuit_detectado=comparacion.cuit_detectado,
            razon_social_seleccionada=(
                comparacion.razon_social_seleccionada
            ),
            razon_social_detectada=(
                comparacion.razon_social_detectada
            ),
            advertencias=list(comparacion.advertencias),
            modo_analisis=getattr(analisis, "modo", None),
        )

    def _validar_documento_op(
        self,
        expediente_id: str,
        documento_op_id: str,
    ) -> None:
        documento = self._documento_service.obtener_por_id(
            documento_op_id
        )
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
    def _resultado_sin_trazabilidad(
        *,
        expediente_id: str,
        documento_op_id: str,
        solicitud_id: str | None,
        estado: EstadoControlProveedorOPAdministrativo,
    ) -> ControlProveedorOPRead:
        return ControlProveedorOPRead(
            expediente_id=expediente_id,
            documento_op_id=documento_op_id,
            solicitud_intervencion_id=solicitud_id,
            seleccion_proveedor_id=None,
            estado=estado,
            cuit_seleccionado=None,
            cuit_detectado=None,
            razon_social_seleccionada=None,
            razon_social_detectada=None,
            advertencias=[],
            modo_analisis=None,
        )
