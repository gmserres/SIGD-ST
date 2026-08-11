from app.domain.seleccion_proveedor import SeleccionProveedor
from app.infrastructure.database.models.seleccion_proveedor_model import SeleccionProveedorModel


def a_modelo(seleccion: SeleccionProveedor) -> SeleccionProveedorModel:
    return SeleccionProveedorModel(
        id_seleccion=seleccion.id_seleccion,
        solicitud_intervencion_id=seleccion.solicitud_intervencion_id,
        decision_administrativa_id=seleccion.decision_administrativa_id,
        proveedor_id=seleccion.proveedor_id,
        fecha_seleccion=seleccion.fecha_seleccion,
        seleccionado_por=seleccion.seleccionado_por,
        proveedor_cuit=seleccion.proveedor_cuit,
        proveedor_razon_social=seleccion.proveedor_razon_social,
        motivo_reemplazo=seleccion.motivo_reemplazo,
        vigente=seleccion.vigente,
    )


def a_dominio(modelo: SeleccionProveedorModel) -> SeleccionProveedor:
    return SeleccionProveedor(
        id_seleccion=modelo.id_seleccion,
        solicitud_intervencion_id=modelo.solicitud_intervencion_id,
        decision_administrativa_id=modelo.decision_administrativa_id,
        proveedor_id=modelo.proveedor_id,
        fecha_seleccion=modelo.fecha_seleccion,
        seleccionado_por=modelo.seleccionado_por,
        proveedor_cuit=modelo.proveedor_cuit,
        proveedor_razon_social=modelo.proveedor_razon_social,
        motivo_reemplazo=modelo.motivo_reemplazo,
        vigente=modelo.vigente,
    )
