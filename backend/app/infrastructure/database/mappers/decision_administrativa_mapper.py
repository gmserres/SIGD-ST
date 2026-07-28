from app.domain.decision_administrativa import DecisionAdministrativa
from app.infrastructure.database.models.decision_administrativa_model import (
    DecisionAdministrativaModel,
)


def a_modelo(
    decision: DecisionAdministrativa,
) -> DecisionAdministrativaModel:
    return DecisionAdministrativaModel(
        id_decision=decision.id_decision,
        solicitud_intervencion_id=decision.solicitud_intervencion_id,
        autoridad_decisora=decision.autoridad_decisora,
        fecha_decision=decision.fecha_decision,
        resultado=decision.resultado,
        fundamento=decision.fundamento,
        fondo_interviniente=decision.fondo_interviniente,
        descripcion_fondo=decision.descripcion_fondo,
        usuario_registrante=decision.usuario_registrante,
    )


def a_dominio(
    modelo: DecisionAdministrativaModel,
) -> DecisionAdministrativa:
    return DecisionAdministrativa(
        id_decision=modelo.id_decision,
        solicitud_intervencion_id=modelo.solicitud_intervencion_id,
        autoridad_decisora=modelo.autoridad_decisora,
        fecha_decision=modelo.fecha_decision,
        resultado=modelo.resultado,
        fundamento=modelo.fundamento,
        fondo_interviniente=modelo.fondo_interviniente,
        descripcion_fondo=modelo.descripcion_fondo,
        usuario_registrante=modelo.usuario_registrante,
    )
