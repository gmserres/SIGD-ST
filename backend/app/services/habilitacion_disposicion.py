from dataclasses import dataclass
from typing import Any

from app.domain.estados import EstadoExpediente


@dataclass(frozen=True)
class MotivoNoHabilitacion:
    codigo: str
    descripcion: str


@dataclass(frozen=True)
class HabilitacionDisposicion:
    habilitada: bool
    motivos: tuple[MotivoNoHabilitacion, ...]


@dataclass(frozen=True)
class ContextoEmisionDisposicion:
    expediente: Any
    decision: Any | None
    analisis_op: Any | None


class EvaluadorHabilitacionDisposicion:
    def __init__(
        self,
        expediente_service,
        decision_service,
        analisis_op_service,
        documento_service,
        validacion_service,
    ) -> None:
        self._expedientes = expediente_service
        self._decisiones = decision_service
        self._analisis_op = analisis_op_service
        self._documentos = documento_service
        self._validacion = validacion_service

    def evaluar(self, expediente_id: str) -> HabilitacionDisposicion:
        resultado, _ = self.evaluar_para_emision(expediente_id)
        return resultado

    def evaluar_para_emision(
        self,
        expediente_id: str,
    ) -> tuple[HabilitacionDisposicion, ContextoEmisionDisposicion]:
        expediente = self._expedientes.obtener(expediente_id)
        motivos: list[MotivoNoHabilitacion] = []

        if expediente.estado == EstadoExpediente.PENDIENTE_REVALIDACION:
            motivos.append(
                MotivoNoHabilitacion(
                    "PENDIENTE_REVALIDACION",
                    "El Expediente requiere una nueva validación "
                    "administrativa.",
                )
            )
        elif expediente.estado != EstadoExpediente.VALIDADO:
            motivos.append(
                MotivoNoHabilitacion(
                    "EXPEDIENTE_NO_VALIDADO",
                    "El Expediente no se encuentra en estado VALIDADO.",
                )
            )

        validacion_vigente = self._validacion.obtener_vigente(
            expediente_id
        )
        if (
            validacion_vigente is None
            and expediente.estado
            != EstadoExpediente.PENDIENTE_REVALIDACION
        ):
            motivos.append(
                MotivoNoHabilitacion(
                    "SIN_VALIDACION_VIGENTE",
                    "El Expediente no posee una validación administrativa "
                    "vigente.",
                )
            )

        documentos = self._documentos.listar_por_expediente(expediente_id)
        tiene_op = any(documento.tipo.upper() == "OP" for documento in documentos)
        if not tiene_op:
            motivos.append(
                MotivoNoHabilitacion(
                    "SIN_OP",
                    "El Expediente no posee una Orden de Pago asociada.",
                )
            )

        decision = None
        datos_insuficientes = any(
            not (getattr(expediente, nombre, None) or "").strip()
            for nombre in (
                "numero_disposicion",
                "objeto",
                "establecimiento",
                "decision_administrativa_id",
            )
        )
        if not datos_insuficientes:
            try:
                decision = self._decisiones.obtener_por_id(
                    expediente.decision_administrativa_id
                )
            except KeyError:
                datos_insuficientes = True
            else:
                if not (decision.fondo_interviniente or "").strip():
                    datos_insuficientes = True

        if not expediente.configuracion_uc_id:
            datos_insuficientes = True

        analisis = None
        if tiene_op and expediente.configuracion_uc_id:
            try:
                analisis = self._analisis_op.analizar(expediente_id)
            except (FileNotFoundError, ValueError):
                analisis = None

            if analisis is None or any(
                valor is None
                or (isinstance(valor, str) and not valor.strip())
                for valor in (
                    getattr(analisis, "orden_pago", None),
                    getattr(analisis, "proveedor", None),
                    getattr(analisis, "cuit", None),
                    getattr(analisis, "importe_bruto", None),
                    getattr(analisis, "valor_uc", None),
                    getattr(analisis, "cantidad_uc", None),
                    getattr(analisis, "procedimiento", None),
                    getattr(analisis, "norma_uc", None),
                )
            ):
                motivos.append(
                    MotivoNoHabilitacion(
                        "OP_NO_APTA",
                        "La Orden de Pago no permite obtener los datos "
                        "necesarios para emitir.",
                    )
                )

        if datos_insuficientes:
            motivos.append(
                MotivoNoHabilitacion(
                    "DATOS_INSUFICIENTES",
                    "Falta información mínima requerida para emitir la "
                    "Disposición.",
                )
            )

        resultado = HabilitacionDisposicion(
            habilitada=not motivos,
            motivos=tuple(motivos),
        )
        return resultado, ContextoEmisionDisposicion(
            expediente=expediente,
            decision=decision,
            analisis_op=analisis,
        )
