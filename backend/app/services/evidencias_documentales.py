from collections.abc import Iterable

from app.schemas.checklist_fisico import ChecklistFisicoRead
from app.schemas.documento import DocumentoRead


def obtener_evidencias_documentales(
    documentos: Iterable[DocumentoRead],
    checklist: ChecklistFisicoRead | None,
    *,
    factura_detectada_en_op: bool = False,
) -> dict[str, bool]:
    tipos = {documento.tipo.upper() for documento in documentos}

    return {
        "factura": (
            factura_detectada_en_op
            or "FACTURA" in tipos
            or "CHECK_FACTURA" in tipos
            or bool(checklist and checklist.factura)
        ),
        "remito_conformidad": (
            bool(
                {
                    "REMITO",
                    "CONFORMIDAD",
                    "ACTA_RECEPCION",
                    "CHECK_REMITO",
                }
                & tipos
            )
            or bool(checklist and checklist.remito_conformidad)
        ),
        "cae": (
            bool({"CAE", "VALIDACION_CAE", "CHECK_CAE"} & tipos)
            or bool(checklist and checklist.cae)
        ),
        "arca": (
            bool({"ARCA", "CHECK_ARCA"} & tipos)
            or bool(checklist and checklist.arca)
        ),
        "arba": (
            bool({"ARBA", "CHECK_ARBA"} & tipos)
            or bool(checklist and checklist.arba)
        ),
    }
