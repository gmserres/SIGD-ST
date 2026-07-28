from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.disposicion import Disposicion
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.repositories.disposicion_repository import (
    DisposicionYaRegistradaError,
)


def verificar_disposicion_duplicada(
    session: Session,
    disposicion: Disposicion,
) -> None:
    criterios = (
        (
            "id",
            disposicion.id_disposicion,
            DisposicionModel.id_disposicion,
        ),
        (
            "expediente",
            disposicion.expediente_id,
            DisposicionModel.expediente_id,
        ),
        (
            "numero_disposicion",
            disposicion.numero_disposicion,
            DisposicionModel.numero_disposicion,
        ),
    )
    for criterio, valor, columna in criterios:
        existente = session.scalar(
            select(DisposicionModel).where(columna == valor)
        )
        if existente is not None:
            raise DisposicionYaRegistradaError(criterio, valor)


def traducir_integrity_error_disposicion(
    error: IntegrityError,
    disposicion: Disposicion,
) -> DisposicionYaRegistradaError | None:
    texto = str(error.orig).lower()
    diagnostico = getattr(error.orig, "diag", None)
    restriccion = (
        getattr(diagnostico, "constraint_name", "") or ""
    )

    if restriccion == "pk_disposiciones":
        return DisposicionYaRegistradaError(
            "id",
            disposicion.id_disposicion,
        )
    if restriccion == "uq_disposiciones_expediente":
        return DisposicionYaRegistradaError(
            "expediente",
            disposicion.expediente_id,
        )
    if restriccion == "uq_disposiciones_numero":
        return DisposicionYaRegistradaError(
            "numero_disposicion",
            disposicion.numero_disposicion,
        )
    if "disposiciones.id_disposicion" in texto:
        return DisposicionYaRegistradaError(
            "id",
            disposicion.id_disposicion,
        )
    if "disposiciones.expediente_id" in texto:
        return DisposicionYaRegistradaError(
            "expediente",
            disposicion.expediente_id,
        )
    if "disposiciones.numero_disposicion" in texto:
        return DisposicionYaRegistradaError(
            "numero_disposicion",
            disposicion.numero_disposicion,
        )
    return None
