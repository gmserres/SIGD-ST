import re
from dataclasses import dataclass, replace


_CUIT_SIN_GUIONES = re.compile(r"^\d{11}$")
_CUIT_CON_GUIONES = re.compile(r"^\d{2}-\d{8}-\d$")


class CuitProveedorDuplicadoError(ValueError):
    pass


def normalizar_cuit(cuit: str) -> str:
    if not isinstance(cuit, str):
        raise TypeError("El CUIT debe ser texto.")

    valor = cuit.strip()
    if not (
        _CUIT_SIN_GUIONES.fullmatch(valor)
        or _CUIT_CON_GUIONES.fullmatch(valor)
    ):
        raise ValueError(
            "El CUIT debe contener exactamente 11 dígitos, "
            "con o sin guiones."
        )

    return valor.replace("-", "")


def normalizar_razon_social(razon_social: str) -> str:
    if not isinstance(razon_social, str):
        raise TypeError("La razón social debe ser texto.")

    valor = razon_social.strip()
    if not valor:
        raise ValueError("La razón social es obligatoria.")
    return valor


@dataclass(frozen=True)
class Proveedor:
    id_proveedor: str
    cuit: str
    razon_social: str
    activo: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.id_proveedor, str):
            raise TypeError(
                "El identificador del proveedor debe ser texto."
            )

        id_proveedor = self.id_proveedor.strip()
        if not id_proveedor:
            raise ValueError(
                "El identificador del proveedor es obligatorio."
            )
        if not isinstance(self.activo, bool):
            raise TypeError("El estado activo debe ser booleano.")

        object.__setattr__(self, "id_proveedor", id_proveedor)
        object.__setattr__(self, "cuit", normalizar_cuit(self.cuit))
        object.__setattr__(
            self,
            "razon_social",
            normalizar_razon_social(self.razon_social),
        )

    def modificar_razon_social(
        self,
        razon_social: str,
    ) -> "Proveedor":
        return replace(self, razon_social=razon_social)

    def activar(self) -> "Proveedor":
        return replace(self, activo=True)

    def inactivar(self) -> "Proveedor":
        return replace(self, activo=False)
