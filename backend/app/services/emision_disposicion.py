from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.core.settings import STORAGE_DIR
from app.domain.disposicion import Disposicion
from app.domain.estados import EstadoExpediente
from app.repositories.emitir_disposicion_persistence import (
    EmitirDisposicionPersistence,
)
from app.schemas.expediente import ExpedienteRead


class EmisionDisposicionError(ValueError):
    pass


class EmisionDisposicionService:
    def __init__(
        self,
        expediente_service,
        decision_service,
        analisis_op_service,
        disposicion_service,
        disposicion_docx_service,
        validacion_service,
        persistence: EmitirDisposicionPersistence,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._expedientes = expediente_service
        self._decisiones = decision_service
        self._analisis_op = analisis_op_service
        self._borradores = disposicion_service
        self._docx = disposicion_docx_service
        self._validacion = validacion_service
        self._persistence = persistence
        self._now = now

    def emitir(self, expediente_id: str) -> ExpedienteRead:
        expediente = self._expedientes.obtener(expediente_id)
        if expediente.estado != EstadoExpediente.VALIDADO:
            raise EmisionDisposicionError(
                "El expediente debe estar VALIDADO antes de emitir."
            )
        errores = self._validacion.errores_bloqueantes(expediente_id)
        if errores:
            raise EmisionDisposicionError(" | ".join(errores))

        for nombre in (
            "numero_disposicion",
            "objeto",
            "establecimiento",
            "decision_administrativa_id",
        ):
            if not (getattr(expediente, nombre) or "").strip():
                raise EmisionDisposicionError(
                    f"Falta {nombre} para emitir la Disposición."
                )

        try:
            decision = self._decisiones.obtener_por_id(
                expediente.decision_administrativa_id
            )
        except KeyError as exc:
            raise EmisionDisposicionError(
                "La Decisión Administrativa no existe."
            ) from exc
        fondo = (decision.fondo_interviniente or "").strip()
        if not fondo:
            raise EmisionDisposicionError(
                "La Decisión no tiene Fondo Interviniente."
            )

        analisis = self._analisis_op.analizar(expediente_id)
        obligatorios = {
            "número de OP": analisis.orden_pago,
            "proveedor": analisis.proveedor,
            "CUIT": analisis.cuit,
            "importe": analisis.importe_bruto,
            "valor UC": analisis.valor_uc,
            "cantidad UC": analisis.cantidad_uc,
            "procedimiento": analisis.procedimiento,
            "norma UC": analisis.norma_uc,
        }
        faltantes = [
            nombre
            for nombre, valor in obligatorios.items()
            if valor is None
            or (isinstance(valor, str) and not valor.strip())
        ]
        if faltantes:
            raise EmisionDisposicionError(
                "Faltan datos para emitir: " + ", ".join(faltantes)
            )

        expediente = self._expedientes.obtener(expediente_id)
        if not expediente.configuracion_uc_id:
            raise EmisionDisposicionError(
                "El Expediente no tiene Configuración UC histórica."
            )

        borrador = self._borradores.obtener(expediente_id)
        texto_emitido = self._docx.construir_texto_emitido(borrador)
        ruta_absoluta = self._docx.generar_docx(expediente_id)
        try:
            ruta_docx = Path(ruta_absoluta).resolve().relative_to(
                STORAGE_DIR.resolve()
            ).as_posix()
        except ValueError as exc:
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
        actualizado = self._persistence.emitir(
            disposicion, expediente_id
        )
        return ExpedienteRead(**asdict(actualizado))
