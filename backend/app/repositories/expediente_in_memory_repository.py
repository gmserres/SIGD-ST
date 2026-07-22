from app.domain.expediente import Expediente


class InMemoryExpedienteRepository:
    def __init__(self) -> None:
        self._expedientes: dict[str, Expediente] = {}
        self._secuencia = 0

    def siguiente_id(self) -> str:
        self._secuencia += 1
        return f"EXP-{self._secuencia:06d}"

    def guardar(self, expediente: Expediente) -> None:
        self._expedientes[expediente.id] = expediente

    def obtener_por_id(self, expediente_id: str) -> Expediente | None:
        return self._expedientes.get(expediente_id)

    def listar(self) -> list[Expediente]:
        return list(self._expedientes.values())
