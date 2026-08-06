from datetime import datetime
from typing import Literal

from app.composition.documento import documento_service
from app.domain.estados import EstadoExpediente
from app.repositories.validacion_administrativa_repository import (
    ValidacionAdministrativaRepository,
)
from app.repositories.validar_expediente_persistence import (
    ValidarExpedientePersistence,
)
from app.schemas.expediente import ExpedienteRead
from app.schemas.validacion import (
    ControlValidacion,
    ControlValidacionSnapshotRead,
    ValidacionAdministrativaRead,
    ValidacionExpedienteRead,
)
from app.composition.expediente import expediente_service
from app.composition.checklist_fisico import checklist_fisico_service
from app.services.evidencias_documentales import obtener_evidencias_documentales


class ValidacionService:
    def __init__(
        self,
        repository: ValidacionAdministrativaRepository | None = None,
        persistence: ValidarExpedientePersistence | None = None,
    ) -> None:
        self._repository = repository
        self._persistence = persistence

    def validar(self, expediente_id: str) -> ValidacionExpedienteRead:
        expediente = expediente_service.obtener(expediente_id)
        documentos = documento_service.listar_por_expediente(expediente_id)
        checklist = checklist_fisico_service.obtener(expediente_id)

        errores: list[str] = []
        advertencias: list[str] = []
        controles: list[ControlValidacion] = []

        def agregar(control: str, ok: bool, observacion_ok: str, observacion_error: str, severidad: str = "ERROR"):
            if ok:
                controles.append(ControlValidacion(control=control, estado="OK", observacion=observacion_ok))
                return
            controles.append(ControlValidacion(control=control, estado=severidad, observacion=observacion_error))
            if severidad == "ERROR":
                errores.append(observacion_error)
            else:
                advertencias.append(observacion_error)

        agregar("Expediente interno", bool(expediente.numero_interno), "Expediente informado.", "Falta número de expediente interno.")
        agregar("Establecimiento", bool(expediente.establecimiento), "Establecimiento informado.", "Falta establecimiento.")
        agregar("Objeto", bool(expediente.objeto), "Objeto informado.", "Falta objeto de la contratación.")

        tipos = {doc.tipo.upper() for doc in documentos}
        tiene_op = "OP" in tipos
        evidencias = obtener_evidencias_documentales(documentos, checklist)

        agregar(
            "Facturas",
            evidencias["factura"] or tiene_op,
            "Facturas acreditadas por archivo, checklist o facturas liquidadas en OP.",
            "Falta acreditar facturas por archivo o checklist.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Remito o conformidad",
            evidencias["remito_conformidad"],
            "Remito, conformidad o acta acreditada.",
            "Falta acreditar remito, conformidad o acta de recepción.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Validación CAE",
            evidencias["cae"],
            "CAE acreditado.",
            "Falta acreditar validación CAE.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Constancia ARCA",
            evidencias["arca"],
            "Constancia ARCA acreditada.",
            "Falta acreditar constancia ARCA.",
            severidad="ADVERTENCIA",
        )

        agregar(
            "Certificado ARBA",
            evidencias["arba"],
            "Certificado ARBA acreditado.",
            "Falta acreditar certificado fiscal ARBA.",
            severidad="ADVERTENCIA",
        )

        estado_general = "ROJO" if errores else ("AMARILLO" if advertencias else "VERDE")

        return ValidacionExpedienteRead(
            expediente_id=expediente_id,
            estado_general=estado_general,
            errores=errores,
            advertencias=advertencias,
            controles=controles,
        )

    def errores_bloqueantes(self, expediente_id: str) -> list[str]:
        return self.validar(expediente_id).errores

    def advertencias_validacion(self, expediente_id: str) -> list[str]:
        return self.validar(expediente_id).advertencias

    def puede_validar_normal(self, expediente_id: str) -> bool:
        resultado = self.validar(expediente_id)
        return not resultado.errores and not resultado.advertencias

    def puede_validar_con_observaciones(self, expediente_id: str) -> bool:
        resultado = self.validar(expediente_id)
        return not resultado.errores and bool(resultado.advertencias)

    def tiene_op(self, expediente_id: str) -> bool:
        documentos = documento_service.listar_por_expediente(expediente_id)
        return any(doc.tipo == "OP" for doc in documentos)

    def registrar(
        self,
        validacion_calculada: ValidacionExpedienteRead,
        resultado: Literal[
            "VALIDADA",
            "VALIDADA_CON_OBSERVACIONES",
        ],
        usuario: str,
        motivo_observacion: str | None = None,
    ) -> ExpedienteRead:
        if self._persistence is None:
            raise RuntimeError(
                "La persistencia de validaciones no está configurada."
            )
        validacion = ValidacionAdministrativaRead(
            expediente_id=validacion_calculada.expediente_id,
            resultado=resultado,
            usuario=usuario,
            fecha_validacion=datetime.now(),
            motivo_observacion=motivo_observacion,
            estado_expediente=EstadoExpediente.VALIDADO.value,
            controles=[
                ControlValidacionSnapshotRead(
                    orden=orden,
                    codigo=control.control,
                    estado=control.estado,
                    observacion=control.observacion,
                )
                for orden, control in enumerate(
                    validacion_calculada.controles
                )
            ],
        )
        expediente, _ = self._persistence.validar(validacion)
        return ExpedienteRead(**expediente.__dict__)

    def obtener_ultima(
        self,
        expediente_id: str,
    ) -> ValidacionAdministrativaRead | None:
        if self._repository is None:
            raise RuntimeError(
                "El repositorio de validaciones no está configurado."
            )
        return self._repository.obtener_ultima_por_expediente(
            expediente_id
        )

    def obtener_vigente(
        self,
        expediente_id: str,
    ) -> ValidacionAdministrativaRead | None:
        if self._repository is None:
            raise RuntimeError(
                "El repositorio de validaciones no está configurado."
            )
        return self._repository.obtener_vigente(expediente_id)

    def listar_actos(
        self,
        expediente_id: str,
    ) -> list[ValidacionAdministrativaRead]:
        if self._repository is None:
            raise RuntimeError(
                "El repositorio de validaciones no está configurado."
            )
        return self._repository.listar_por_expediente(expediente_id)
