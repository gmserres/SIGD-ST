from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TypeAlias


ConfiguracionUCId: TypeAlias = str
RangoProcedimientoUCId: TypeAlias = str


@dataclass(frozen=True)
class RangoProcedimientoUC:
    id_rango: RangoProcedimientoUCId
    configuracion_uc_id: ConfiguracionUCId
    limite_inferior: Decimal
    limite_superior: Decimal
    limite_inferior_inclusivo: bool
    limite_superior_inclusivo: bool
    procedimiento: str
    articulo: str
    inciso: str
    referencia_normativa: str

    def __post_init__(self) -> None:
        if not self.id_rango.strip():
            raise ValueError("El identificador del rango es obligatorio.")
        if not self.configuracion_uc_id.strip():
            raise ValueError(
                "El identificador de la Configuración UC es obligatorio."
            )
        if self.limite_superior <= self.limite_inferior:
            raise ValueError(
                "El límite superior debe ser mayor que el límite inferior."
            )
        if not self.procedimiento.strip():
            raise ValueError("El procedimiento es obligatorio.")
        if not self.articulo.strip():
            raise ValueError("El artículo es obligatorio.")
        if not self.inciso.strip():
            raise ValueError("El inciso es obligatorio.")
        if not self.referencia_normativa.strip():
            raise ValueError("La referencia normativa es obligatoria.")


@dataclass(frozen=True)
class ConfiguracionUC:
    id_configuracion: ConfiguracionUCId
    fecha_inicio_vigencia: date
    fecha_fin_vigencia: date | None
    valor_uc: Decimal
    moneda: str
    resolucion: str
    organismo_emisor: str
    estado: str
    rangos: tuple[RangoProcedimientoUC, ...]

    def __post_init__(self) -> None:
        if not self.id_configuracion.strip():
            raise ValueError(
                "El identificador de la Configuración UC es obligatorio."
            )
        if self.fecha_inicio_vigencia is None:
            raise ValueError("La fecha de inicio de vigencia es obligatoria.")
        if (
            self.fecha_fin_vigencia is not None
            and self.fecha_fin_vigencia < self.fecha_inicio_vigencia
        ):
            raise ValueError(
                "La fecha de fin de vigencia no puede ser anterior "
                "a la fecha de inicio."
            )
        if self.valor_uc <= Decimal("0"):
            raise ValueError("El valor UC debe ser mayor que cero.")
        if not self.moneda.strip():
            raise ValueError("La moneda es obligatoria.")
        if not self.resolucion.strip():
            raise ValueError("La resolución es obligatoria.")
        if not self.organismo_emisor.strip():
            raise ValueError("El organismo emisor es obligatorio.")
        if not self.estado.strip():
            raise ValueError("El estado es obligatorio.")
        if not self.rangos:
            raise ValueError(
                "La Configuración UC debe contener al menos un rango."
            )

        rangos_ordenados = tuple(
            sorted(
                self.rangos,
                key=lambda rango: (
                    rango.limite_inferior,
                    rango.limite_superior,
                    rango.id_rango,
                ),
            )
        )
        object.__setattr__(self, "rangos", rangos_ordenados)
        self._validar_rangos()

    def _validar_rangos(self) -> None:
        for rango in self.rangos:
            if rango.configuracion_uc_id != self.id_configuracion:
                raise ValueError(
                    "Todos los rangos deben pertenecer exclusivamente "
                    "a la Configuración UC."
                )

        for anterior, actual in zip(self.rangos, self.rangos[1:]):
            if actual.limite_inferior < anterior.limite_superior:
                raise ValueError(
                    "Los rangos de la Configuración UC no pueden superponerse."
                )
            if actual.limite_inferior > anterior.limite_superior:
                raise ValueError(
                    "Los rangos de la Configuración UC deben ser continuos."
                )
            if (
                anterior.limite_superior_inclusivo
                and actual.limite_inferior_inclusivo
            ):
                raise ValueError(
                    "Un límite compartido no puede pertenecer a dos rangos."
                )
            if (
                not anterior.limite_superior_inclusivo
                and not actual.limite_inferior_inclusivo
            ):
                raise ValueError(
                    "Un límite compartido debe pertenecer a uno de los rangos."
                )


class VigenciaConfiguracionUCSuperpuestaError(ValueError):
    pass


def validar_vigencias_no_superpuestas(
    configuracion: ConfiguracionUC,
    existentes: list[ConfiguracionUC],
) -> None:
    inicio = configuracion.fecha_inicio_vigencia
    fin = configuracion.fecha_fin_vigencia or date.max

    for existente in existentes:
        if existente.id_configuracion == configuracion.id_configuracion:
            continue

        inicio_existente = existente.fecha_inicio_vigencia
        fin_existente = existente.fecha_fin_vigencia or date.max

        if inicio <= fin_existente and inicio_existente <= fin:
            raise VigenciaConfiguracionUCSuperpuestaError(
                "La vigencia de la Configuración UC se superpone "
                "con otra configuración existente."
            )
