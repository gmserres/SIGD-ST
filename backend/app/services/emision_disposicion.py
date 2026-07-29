from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.core.settings import STORAGE_DIR
from app.domain.disposicion import Disposicion
from app.repositories.emitir_disposicion_persistence import (
    EmitirDisposicionPersistence,
)
from app.schemas.expediente import ExpedienteRead
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
    def __init__(
        self,
        detalle: HabilitacionDisposicion | str,
    ) -> None:
        if isinstance(detalle, HabilitacionDisposicion):
            self.habilitacion = detalle
            mensaje = " | ".join(
                motivo.descripcion for motivo in detalle.motivos
            )
        else:
            self.habilitacion = None
            mensaje = detalle
        super().__init__(mensaje)


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

    def emitir(self, expediente_id: str) -> ExpedienteRead:
        habilitacion, contexto = (
            self._evaluador_habilitacion.evaluar_para_emision(
                expediente_id
            )
        )
        if not habilitacion.habilitada:
            raise EmisionDisposicionError(habilitacion)
        expediente = contexto.expediente
        decision = contexto.decision
        analisis = contexto.analisis_op
        fondo = decision.fondo_interviniente.strip()

        borrador = self._borradores.obtener(expediente_id)
        texto_emitido = self._docx.construir_texto_emitido(borrador)
        ruta_absoluta = self._docx.generar_docx(expediente_id)
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

        disposicion = Disposicion(
            id_disposicion=str(uuid4()),
            expediente_id=expediente_id,
            configuracion_uc_id=expediente.configuracion_uc_id,
            numero_disposicion=expediente.numero_disposicion,
            fecha_emision=self._now(),
            fondo_interviniente=fondo,
            numero_op=analisis.orden_pago,
            numero_liquidacion=analisis.liquidacion,
            proveedor=analisis.proveedor,
            cuit=analisis.cuit,
            importe=Decimal(str(analisis.importe_bruto)),
            objeto=expediente.objeto,
            establecimiento=expediente.establecimiento,
            valor_uc_aplicado=Decimal(analisis.valor_uc),
            cantidad_uc=Decimal(analisis.cantidad_uc),
            procedimiento_contratacion=analisis.procedimiento,
            norma_uc=analisis.norma_uc,
            texto_emitido=texto_emitido,
            ruta_docx=ruta_docx,
        )
        try:
            actualizado = self._persistence.emitir(
                disposicion, expediente_id
            )
        except Exception:
            _eliminar_docx_generado(ruta_generada)
            raise
        return ExpedienteRead(**asdict(actualizado))
