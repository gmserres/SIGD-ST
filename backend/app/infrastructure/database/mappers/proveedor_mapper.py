from app.domain.proveedor import Proveedor
from app.infrastructure.database.models.proveedor_model import (
    ProveedorModel,
)


def a_modelo(proveedor: Proveedor) -> ProveedorModel:
    return ProveedorModel(
        id_proveedor=proveedor.id_proveedor,
        cuit=proveedor.cuit,
        razon_social=proveedor.razon_social,
        activo=proveedor.activo,
    )


def a_dominio(modelo: ProveedorModel) -> Proveedor:
    return Proveedor(
        id_proveedor=modelo.id_proveedor,
        cuit=modelo.cuit,
        razon_social=modelo.razon_social,
        activo=modelo.activo,
    )


def actualizar_modelo(
    modelo: ProveedorModel,
    proveedor: Proveedor,
) -> None:
    modelo.razon_social = proveedor.razon_social
    modelo.activo = proveedor.activo
