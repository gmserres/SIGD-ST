from dataclasses import dataclass, replace
from datetime import datetime

from app.domain.proveedor import normalizar_cuit


class SeleccionProveedorError(ValueError):
    pass


class SeleccionProveedorVigenteError(SeleccionProveedorError):
    pass


class SeleccionProveedorInexistenteError(LookupError):
    pass


class SolicitudSeleccionInexistenteError(LookupError):
    pass


class ExpedienteSeleccionInexistenteError(LookupError):
    pass


class ExpedienteSeleccionIncompletoError(SeleccionProveedorError):
    pass


class DecisionSeleccionInexistenteError(LookupError):
    pass


class DecisionNoAprobatoriaError(SeleccionProveedorError):
    pass


class DecisionSolicitudInconsistenteError(SeleccionProveedorError):
    pass


class FondoSeleccionIncompatibleError(SeleccionProveedorError):
    pass


class ProveedorSeleccionInexistenteError(LookupError):
    pass


class ProveedorInactivoError(SeleccionProveedorError):
    pass


class MismoProveedorSeleccionadoError(SeleccionProveedorError):
    pass


@dataclass(frozen=True)
class SeleccionProveedor:
    id_seleccion: str
    expediente_id: str
    solicitud_intervencion_id: str
    decision_administrativa_id: str
    proveedor_id: str
    fecha_seleccion: datetime
    seleccionado_por: str
    proveedor_cuit: str
    proveedor_razon_social: str
    motivo_reemplazo: str | None
    vigente: bool

    def __post_init__(self) -> None:
        campos_textuales = (
            "id_seleccion",
            "expediente_id",
            "solicitud_intervencion_id",
            "decision_administrativa_id",
            "proveedor_id",
            "seleccionado_por",
            "proveedor_razon_social",
        )

        for nombre in campos_textuales:
            valor = getattr(self, nombre)
            if not isinstance(valor, str):
                raise TypeError(f"{nombre} debe ser texto.")

            valor_normalizado = valor.strip()
            if not valor_normalizado:
                raise ValueError(f"{nombre} es obligatorio.")

            object.__setattr__(self, nombre, valor_normalizado)

        if not isinstance(self.fecha_seleccion, datetime):
            raise TypeError("fecha_seleccion debe ser datetime.")

        if not isinstance(self.vigente, bool):
            raise TypeError("vigente debe ser booleano.")

        object.__setattr__(
            self,
            "proveedor_cuit",
            normalizar_cuit(self.proveedor_cuit),
        )

        if self.motivo_reemplazo is not None:
            if not isinstance(self.motivo_reemplazo, str):
                raise TypeError("motivo_reemplazo debe ser texto.")

            motivo_normalizado = self.motivo_reemplazo.strip()
            if not motivo_normalizado:
                raise ValueError(
                    "motivo_reemplazo no puede estar vacío."
                )

            object.__setattr__(
                self,
                "motivo_reemplazo",
                motivo_normalizado,
            )

    def finalizar_vigencia(self) -> "SeleccionProveedor":
        if not self.vigente:
            return self
        return replace(self, vigente=False)
