from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.configuracion_uc.obtener_configuracion_uc_vigente import (
    ObtenerConfiguracionUCVigente,
)
from app.domain.configuracion_uc import (
    ConfiguracionUC,
    ConfiguracionUCId,
    RangoProcedimientoUC,
    RangoProcedimientoUCId,
)


@dataclass(frozen=True)
class ResultadoDeterminacionProcedimiento:
    monto: Decimal
    cantidad_uc: Decimal
    valor_uc: Decimal
    configuracion: ConfiguracionUC
    rango: RangoProcedimientoUC


class MontoDeterminacionProcedimientoNegativoError(ValueError):
    def __init__(self, monto: Decimal) -> None:
        self.monto = monto
        super().__init__(
            "El monto utilizado para determinar el procedimiento "
            "no puede ser negativo."
        )


class RangoProcedimientoUCNoEncontradoError(LookupError):
    def __init__(
        self,
        cantidad_uc: Decimal,
        configuracion_id: ConfiguracionUCId,
    ) -> None:
        self.cantidad_uc = cantidad_uc
        self.configuracion_id = configuracion_id
        super().__init__(
            "No existe un rango de procedimiento aplicable para "
            f"{cantidad_uc} UC en la Configuración UC "
            f"{configuracion_id}."
        )


class MultiplesRangosProcedimientoUCError(ValueError):
    def __init__(
        self,
        cantidad_uc: Decimal,
        configuracion_id: ConfiguracionUCId,
        rango_ids: tuple[RangoProcedimientoUCId, ...],
    ) -> None:
        self.cantidad_uc = cantidad_uc
        self.configuracion_id = configuracion_id
        self.rango_ids = rango_ids
        identificadores = ", ".join(
            str(rango_id) for rango_id in rango_ids
        )
        super().__init__(
            "Existe más de un rango de procedimiento aplicable para "
            f"{cantidad_uc} UC en la Configuración UC "
            f"{configuracion_id}: {identificadores}."
        )


class DeterminarProcedimientoContratacion:
    def __init__(
        self,
        obtener_configuracion_vigente: ObtenerConfiguracionUCVigente,
    ) -> None:
        self._obtener_configuracion_vigente = (
            obtener_configuracion_vigente
        )

    def ejecutar(
        self,
        fecha: date,
        monto: Decimal,
    ) -> ResultadoDeterminacionProcedimiento:
        self._validar_monto(monto)
        configuracion = (
            self._obtener_configuracion_vigente.ejecutar(fecha)
        )
        return self.ejecutar_con_configuracion(
            configuracion=configuracion,
            monto=monto,
        )

    def ejecutar_con_configuracion(
        self,
        configuracion: ConfiguracionUC,
        monto: Decimal,
    ) -> ResultadoDeterminacionProcedimiento:
        self._validar_monto(monto)
        cantidad_uc = monto / configuracion.valor_uc
        rangos_aplicables = tuple(
            rango
            for rango in configuracion.rangos
            if self._contiene(rango, cantidad_uc)
        )

        if not rangos_aplicables:
            raise RangoProcedimientoUCNoEncontradoError(
                cantidad_uc,
                configuracion.id_configuracion,
            )

        if len(rangos_aplicables) > 1:
            raise MultiplesRangosProcedimientoUCError(
                cantidad_uc,
                configuracion.id_configuracion,
                tuple(
                    rango.id_rango
                    for rango in rangos_aplicables
                ),
            )

        return ResultadoDeterminacionProcedimiento(
            monto=monto,
            cantidad_uc=cantidad_uc,
            valor_uc=configuracion.valor_uc,
            configuracion=configuracion,
            rango=rangos_aplicables[0],
        )

    @staticmethod
    def _validar_monto(monto: Decimal) -> None:
        if monto < Decimal("0"):
            raise MontoDeterminacionProcedimientoNegativoError(monto)

    @staticmethod
    def _contiene(
        rango: RangoProcedimientoUC,
        cantidad_uc: Decimal,
    ) -> bool:
        limite_inferior_cumplido = (
            cantidad_uc >= rango.limite_inferior
            if rango.limite_inferior_inclusivo
            else cantidad_uc > rango.limite_inferior
        )
        limite_superior_cumplido = (
            cantidad_uc <= rango.limite_superior
            if rango.limite_superior_inclusivo
            else cantidad_uc < rango.limite_superior
        )
        return (
            limite_inferior_cumplido
            and limite_superior_cumplido
        )
