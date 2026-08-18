from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.composition.habilitacion_proveedor_op import (
    evaluar_habilitacion_proveedor_op_service,
)
from app.composition.seleccion_proveedor import seleccion_proveedor_repository
from app.core.settings import STORAGE_DIR
from app.domain.disposicion import Disposicion
from app.domain.habilitacion_proveedor_op import EstadoHabilitacionProveedorOP
from app.repositories.emitir_disposicion_persistence import (
    EmitirDisposicionPersistence,
)
from app.schemas.disposicion import DisposicionEmitidaRead
from app.schemas.expediente import ExpedienteRead
from app.services.disposiciones import BorradorDisposicionObsoletoError
from app.services.habilitacion_disposicion import (
    EvaluadorHabilitacionDisposicion,
    HabilitacionDisposicion,
)


def _eliminar_docx_generado(ruta: Path) -> None:
    try:
        ruta.unlink(missing_ok=True)
    except OSError:
        pass


class EmisionDisposicionError(ValueError):
    def __init__(self, detalle: HabilitacionDisposicion | str) -> None:
        if isinstance(detalle, HabilitacionDisposicion):
            self.habilitacion = detalle
            mensaje = " | ".join(
                motivo.descripcion for motivo in detalle.motivos
            )
        else:
            self.habilitacion = None
            mensaje = detalle
        super().__init__(mensaje)


class EmisionProveedorOPNoHabilitadoError(ValueError):
    def __init__(self, habilitacion) -> None:
        self.habilitacion = habilitacion
        super().__init__(habilitacion.mensaje)


class EmisionDisposicionService:
    def __init__(
        self,
        evaluador_habilitacion: EvaluadorHabilitacionDisposicion,
        disposicion_service,
        disposicion_docx_service,
        persistence: EmitirDisposicionPersistence,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._evaluador_habilitacion = evaluador_habilitacion
        self._borradores = disposicion_service
        self._docx = disposicion_docx_service
        self._persistence = persistence
        self._now = now

    def emitir(
        self,
        expediente_id: str,
        documento_op_id: str | None = None,
        numero_disposicion: str | None = None,
    ) -> DisposicionEmitidaRead | ExpedienteRead:
        if documento_op_id is None and numero_disposicion is None:
            return self.emitir_legacy(expediente_id)
        if documento_op_id is None or numero_disposicion is None:
            raise TypeError(
                "documento_op_id y numero_disposicion son obligatorios."
            )
        numero = numero_disposicion.strip()
        if not numero:
            raise EmisionDisposicionError(
                "El número de Disposición es obligatorio."
            )

        habilitacion_general, contexto = (
            self._evaluador_habilitacion.evaluar_para_emision_documento(
                expediente_id, documento_op_id
            )
        )
        if not habilitacion_general.habilitada:
            raise EmisionDisposicionError(habilitacion_general)

        habilitacion = evaluar_habilitacion_proveedor_op_service.evaluar(
            expediente_id, documento_op_id
        )
        if habilitacion.estado != EstadoHabilitacionProveedorOP.HABILITADO:
            raise EmisionProveedorOPNoHabilitadoError(habilitacion)

        borrador = self._borradores.obtener_exportable(
            expediente_id, documento_op_id
        )
        if not self._mismo_contexto(borrador, habilitacion):
            raise BorradorDisposicionObsoletoError(documento_op_id)

        proveedor_presentacion = (
            habilitacion.proveedor_definitivo_razon_social
        )
        if proveedor_presentacion is None:
            seleccion = seleccion_proveedor_repository.obtener_por_id(
                habilitacion.seleccion_proveedor_id
            )
            if (
                seleccion is None
                or seleccion.id_seleccion
                != habilitacion.seleccion_proveedor_id
                or seleccion.expediente_id != expediente_id
            ):
                raise BorradorDisposicionObsoletoError(documento_op_id)
            proveedor_presentacion = seleccion.proveedor_razon_social

        id_disposicion = str(uuid4())
        texto_emitido = self._docx.construir_texto_emitido(
            borrador
        ).replace("____/____", numero)
        ruta_absoluta = self._docx.generar_docx_definitivo(
            expediente_id,
            documento_op_id,
            id_disposicion,
            numero,
            borrador,
        )
        ruta_generada = Path(ruta_absoluta).resolve()
        try:
            ruta_docx = ruta_generada.relative_to(
                STORAGE_DIR.resolve()
            ).as_posix()
        except ValueError as exc:
            _eliminar_docx_generado(ruta_generada)
            raise EmisionDisposicionError(
                "El DOCX fue generado fuera del almacenamiento permitido."
            ) from exc

        analisis = contexto.analisis_op
        expediente = contexto.expediente
        disposicion = Disposicion(
            id_disposicion=id_disposicion,
            expediente_id=expediente_id,
            configuracion_uc_id=expediente.configuracion_uc_id,
            numero_disposicion=numero,
            fecha_emision=self._now(),
            fondo_interviniente=(
                contexto.decision.fondo_interviniente.strip()
            ),
            numero_op=analisis.orden_pago,
            numero_liquidacion=analisis.liquidacion,
            proveedor=proveedor_presentacion,
            cuit=habilitacion.proveedor_definitivo_cuit,
            importe=Decimal(str(analisis.importe_bruto)),
            objeto=expediente.objeto,
            establecimiento=expediente.establecimiento,
            valor_uc_aplicado=Decimal(str(analisis.valor_uc)),
            cantidad_uc=Decimal(str(analisis.cantidad_uc)),
            procedimiento_contratacion=analisis.procedimiento,
            norma_uc=analisis.norma_uc,
            texto_emitido=texto_emitido,
            ruta_docx=ruta_docx,
            documento_op_id=documento_op_id,
            control_proveedor_op_id=habilitacion.control_proveedor_op_id,
            seleccion_proveedor_id=habilitacion.seleccion_proveedor_id,
            proveedor_definitivo_id=habilitacion.proveedor_definitivo_id,
            proveedor_definitivo_cuit=(
                habilitacion.proveedor_definitivo_cuit
            ),
            proveedor_definitivo_razon_social=(
                habilitacion.proveedor_definitivo_razon_social
            ),
        )
        try:
            guardada = self._persistence.emitir(disposicion, expediente_id)
        except Exception:
            _eliminar_docx_generado(ruta_generada)
            raise
        return DisposicionEmitidaRead(**asdict(guardada))

    def emitir_legacy(self, expediente_id: str) -> ExpedienteRead:
        habilitacion, contexto = (
            self._evaluador_habilitacion.evaluar_para_emision(expediente_id)
        )
        if not habilitacion.habilitada:
            raise EmisionDisposicionError(habilitacion)
        expediente = contexto.expediente
        analisis = contexto.analisis_op
        borrador = self._borradores.obtener(expediente_id)
        texto_emitido = self._docx.construir_texto_emitido(borrador)
        ruta_generada = Path(
            self._docx.generar_docx(expediente_id)
        ).resolve()
        try:
            ruta_docx = ruta_generada.relative_to(
                STORAGE_DIR.resolve()
            ).as_posix()
        except ValueError as exc:
            _eliminar_docx_generado(ruta_generada)
            raise EmisionDisposicionError(
                "El DOCX fue generado fuera del almacenamiento permitido."
            ) from exc
        disposicion = Disposicion(
            id_disposicion=str(uuid4()),
            expediente_id=expediente_id,
            configuracion_uc_id=expediente.configuracion_uc_id,
            numero_disposicion=expediente.numero_disposicion,
            fecha_emision=self._now(),
            fondo_interviniente=contexto.decision.fondo_interviniente.strip(),
            numero_op=analisis.orden_pago,
            numero_liquidacion=analisis.liquidacion,
            proveedor=analisis.proveedor,
            cuit=analisis.cuit,
            importe=Decimal(str(analisis.importe_bruto)),
            objeto=expediente.objeto,
            establecimiento=expediente.establecimiento,
            valor_uc_aplicado=Decimal(str(analisis.valor_uc)),
            cantidad_uc=Decimal(str(analisis.cantidad_uc)),
            procedimiento_contratacion=analisis.procedimiento,
            norma_uc=analisis.norma_uc,
            texto_emitido=texto_emitido,
            ruta_docx=ruta_docx,
        )
        try:
            actualizado = self._persistence.emitir(disposicion, expediente_id)
        except Exception:
            _eliminar_docx_generado(ruta_generada)
            raise
        return ExpedienteRead(**asdict(actualizado))

    @staticmethod
    def _mismo_contexto(borrador, habilitacion) -> bool:
        return all((
            borrador.documento_op_id == habilitacion.documento_op_id,
            borrador.control_proveedor_op_id
            == habilitacion.control_proveedor_op_id,
            borrador.seleccion_proveedor_id
            == habilitacion.seleccion_proveedor_id,
            borrador.proveedor_definitivo_id
            == habilitacion.proveedor_definitivo_id,
            borrador.proveedor_definitivo_cuit
            == habilitacion.proveedor_definitivo_cuit,
            borrador.proveedor_definitivo_razon_social
            == habilitacion.proveedor_definitivo_razon_social,
        ))
