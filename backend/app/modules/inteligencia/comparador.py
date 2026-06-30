from dataclasses import dataclass


@dataclass
class ResultadoComparacion:
    estado: str
    total_op: float | None
    total_facturas: float | None
    diferencia: float | None
    mensaje: str


def comparar_total_facturas(*, total_op: float | None, facturas: list) -> ResultadoComparacion:
    if total_op is None:
        return ResultadoComparacion(
            estado="SIN_TOTAL_OP",
            total_op=None,
            total_facturas=None,
            diferencia=None,
            mensaje="No se detectó monto total de OP para comparar.",
        )

    if not facturas:
        return ResultadoComparacion(
            estado="SIN_FACTURAS",
            total_op=total_op,
            total_facturas=None,
            diferencia=None,
            mensaje="No se detectaron facturas liquidadas para comparar.",
        )

    total_facturas = round(sum(getattr(f, "importe", 0) for f in facturas), 2)
    diferencia = round(total_facturas - total_op, 2)

    if abs(diferencia) <= 1:
        return ResultadoComparacion(
            estado="CONSISTENTE",
            total_op=total_op,
            total_facturas=total_facturas,
            diferencia=0,
            mensaje="La suma de facturas coincide con el monto total informado en la OP.",
        )

    return ResultadoComparacion(
        estado="INCONSISTENTE",
        total_op=total_op,
        total_facturas=total_facturas,
        diferencia=diferencia,
        mensaje="La suma de facturas no coincide con el monto total informado en la OP.",
    )
