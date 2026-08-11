from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.disposicion import Disposicion
from app.infrastructure.database.models.disposicion_model import (
    DisposicionModel,
)
from app.infrastructure.database.mappers.control_proveedor_op_mapper import (
    documento_id_a_secuencia,
)
from app.repositories.disposicion_repository import (
    DisposicionYaRegistradaError,
)


def verificar_disposicion_duplicada(
    session: Session,
    disposicion: Disposicion,
) -> None:
    criterios = [
        (
            "id",
            disposicion.id_disposicion,
            DisposicionModel.id_disposicion,
        ),
        (
            "numero_disposicion",
            disposicion.numero_disposicion,
            DisposicionModel.numero_disposicion,
        ),
    ]
    if disposicion.documento_op_id is not None:
        criterios.append(
            (
                "documento_op",
                documento_id_a_secuencia(disposicion.documento_op_id),
                DisposicionModel.documento_op_secuencia,
            )
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
    if restriccion == "uq_disposiciones_documento_op":
        return DisposicionYaRegistradaError(
            "documento_op",
            disposicion.documento_op_id or "",
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
    if "disposiciones.documento_op_secuencia" in texto:
        return DisposicionYaRegistradaError(
            "documento_op",
            disposicion.documento_op_id or "",
        )
    return None
