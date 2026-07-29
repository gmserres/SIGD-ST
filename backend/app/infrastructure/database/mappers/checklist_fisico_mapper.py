from app.infrastructure.database.models.checklist_fisico_model import (
    ChecklistFisicoModel,
)
from app.schemas.checklist_fisico import ChecklistFisicoRead


def a_modelo(checklist: ChecklistFisicoRead) -> ChecklistFisicoModel:
    return ChecklistFisicoModel(
        expediente_id=checklist.expediente_id,
        factura=checklist.factura,
        remito_conformidad=checklist.remito_conformidad,
        cae=checklist.cae,
        arca=checklist.arca,
        arba=checklist.arba,
        observaciones=checklist.observaciones,
        usuario=checklist.usuario,
        fecha_registro=checklist.fecha,
    )


def actualizar_modelo(
    modelo: ChecklistFisicoModel,
    checklist: ChecklistFisicoRead,
) -> None:
    modelo.factura = checklist.factura
    modelo.remito_conformidad = checklist.remito_conformidad
    modelo.cae = checklist.cae
    modelo.arca = checklist.arca
    modelo.arba = checklist.arba
    modelo.observaciones = checklist.observaciones
    modelo.usuario = checklist.usuario
    modelo.fecha_registro = checklist.fecha


def a_schema(modelo: ChecklistFisicoModel) -> ChecklistFisicoRead:
    return ChecklistFisicoRead(
        expediente_id=modelo.expediente_id,
        factura=modelo.factura,
        remito_conformidad=modelo.remito_conformidad,
        cae=modelo.cae,
        arca=modelo.arca,
        arba=modelo.arba,
        observaciones=modelo.observaciones,
        usuario=modelo.usuario,
        fecha=modelo.fecha_registro,
    )
