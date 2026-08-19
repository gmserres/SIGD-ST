from enum import Enum


ESTADOS_TERMINALES_ORDINARIOS = frozenset({"CERRADO", "DESISTIDO"})


class ExpedienteTerminalError(ValueError):
    def __init__(self, expediente_id: str, estado: str) -> None:
        super().__init__(
            f"El Expediente {expediente_id} se encuentra {estado} y no admite "
            "nuevas actuaciones administrativas."
        )


class EstadoHabilitacionCierre(str, Enum):
    HABILITADO = "HABILITADO"
    YA_CERRADO = "YA_CERRADO"
    YA_DESISTIDO = "YA_DESISTIDO"
    ARCHIVADO = "ARCHIVADO"
    ESTADO_NO_APTO = "ESTADO_NO_APTO"
    SIN_OP = "SIN_OP"
    OP_SIN_DISPOSICION = "OP_SIN_DISPOSICION"
    DISPOSICION_SIN_FORMALIZAR = "DISPOSICION_SIN_FORMALIZAR"


class EstadoHabilitacionDesistimiento(str, Enum):
    HABILITADO = "HABILITADO"
    YA_DESISTIDO = "YA_DESISTIDO"
    YA_CERRADO = "YA_CERRADO"
    ARCHIVADO = "ARCHIVADO"
    ESTADO_NO_APTO = "ESTADO_NO_APTO"
    TIENE_OP = "TIENE_OP"
