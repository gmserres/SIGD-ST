import unicodedata
from dataclasses import dataclass
from enum import Enum

from app.domain.proveedor import normalizar_cuit


ADVERTENCIA_RAZON_SOCIAL_DIFERENTE = (
    "La razón social detectada en la Orden de Pago difiere de la "
    "razón social del proveedor seleccionado."
)
ADVERTENCIA_RAZON_SOCIAL_NO_VERIFICABLE = (
    "La Orden de Pago no informa una razón social verificable."
)


class EstadoControlProveedorOP(str, Enum):
    COINCIDE = "COINCIDE"
    CUIT_DIFERENTE = "CUIT_DIFERENTE"
    NO_VERIFICABLE = "NO_VERIFICABLE"


@dataclass(frozen=True)
class ControlProveedorOPResultado:
    estado: EstadoControlProveedorOP
    cuit_seleccionado: str
    cuit_detectado: str | None
    razon_social_seleccionada: str
    razon_social_detectada: str | None
    advertencias: tuple[str, ...]


def comparar_proveedor_op(
    *,
    proveedor_cuit: str,
    proveedor_razon_social: str,
    cuit_detectado: str | None,
    razon_social_detectada: str | None,
) -> ControlProveedorOPResultado:
    cuit_seleccionado_normalizado = normalizar_cuit(
        proveedor_cuit
    )
    razon_social_seleccionada = (
        _preparar_razon_social_seleccionada(
            proveedor_razon_social
        )
    )
    razon_social_op = _preparar_razon_social_detectada(
        razon_social_detectada
    )
    cuit_op = _normalizar_cuit_detectado(cuit_detectado)

    if cuit_op is None:
        return ControlProveedorOPResultado(
            estado=EstadoControlProveedorOP.NO_VERIFICABLE,
            cuit_seleccionado=cuit_seleccionado_normalizado,
            cuit_detectado=None,
            razon_social_seleccionada=(
                razon_social_seleccionada
            ),
            razon_social_detectada=razon_social_op,
            advertencias=(),
        )

    if cuit_op != cuit_seleccionado_normalizado:
        return ControlProveedorOPResultado(
            estado=EstadoControlProveedorOP.CUIT_DIFERENTE,
            cuit_seleccionado=cuit_seleccionado_normalizado,
            cuit_detectado=cuit_op,
            razon_social_seleccionada=(
                razon_social_seleccionada
            ),
            razon_social_detectada=razon_social_op,
            advertencias=(),
        )

    advertencias = _comparar_razones_sociales(
        razon_social_seleccionada,
        razon_social_op,
    )
    return ControlProveedorOPResultado(
        estado=EstadoControlProveedorOP.COINCIDE,
        cuit_seleccionado=cuit_seleccionado_normalizado,
        cuit_detectado=cuit_op,
        razon_social_seleccionada=razon_social_seleccionada,
        razon_social_detectada=razon_social_op,
        advertencias=advertencias,
    )


def _normalizar_cuit_detectado(
    cuit_detectado: str | None,
) -> str | None:
    if cuit_detectado is None:
        return None
    if not isinstance(cuit_detectado, str):
        raise TypeError("El CUIT detectado debe ser texto.")
    if not cuit_detectado.strip():
        return None

    try:
        return normalizar_cuit(cuit_detectado)
    except ValueError:
        return None


def _preparar_razon_social_seleccionada(
    razon_social: str,
) -> str:
    if not isinstance(razon_social, str):
        raise TypeError(
            "La razón social seleccionada debe ser texto."
        )
    valor = razon_social.strip()
    if not valor:
        raise ValueError(
            "La razón social seleccionada es obligatoria."
        )
    return valor


def _preparar_razon_social_detectada(
    razon_social: str | None,
) -> str | None:
    if razon_social is None:
        return None
    if not isinstance(razon_social, str):
        raise TypeError(
            "La razón social detectada debe ser texto."
        )
    return razon_social.strip() or None


def _comparar_razones_sociales(
    seleccionada: str,
    detectada: str | None,
) -> tuple[str, ...]:
    if detectada is None:
        return (ADVERTENCIA_RAZON_SOCIAL_NO_VERIFICABLE,)
    if (
        _normalizar_razon_social_para_comparacion(seleccionada)
        != _normalizar_razon_social_para_comparacion(detectada)
    ):
        return (ADVERTENCIA_RAZON_SOCIAL_DIFERENTE,)
    return ()


def _normalizar_razon_social_para_comparacion(
    razon_social: str,
) -> str:
    sin_puntuacion = "".join(
        caracter
        for caracter in razon_social.casefold()
        if not unicodedata.category(caracter).startswith("P")
    )
    return " ".join(sin_puntuacion.split())
