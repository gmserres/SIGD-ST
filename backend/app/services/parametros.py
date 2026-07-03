from app.schemas.parametros import ParametrosInstitucionalesRead, ParametrosInstitucionalesUpdate


class ParametrosInstitucionalesService:
    def __init__(self) -> None:
        self._parametros = ParametrosInstitucionalesRead(
            ejercicio=2025,
            valor_uc=1677.0,
            norma_uc="RESO-2024-32-GDEBA-OPCGP",
            fecha_vigencia_uc="01/01/2025",
            distrito="GENERAL ALVARADO",
            localidad="Miramar",
            organismo="Consejo Escolar de Gral. Alvarado",
            proxima_disposicion=185,
        )

    def obtener(self) -> ParametrosInstitucionalesRead:
        return self._parametros

    def actualizar(self, data: ParametrosInstitucionalesUpdate) -> ParametrosInstitucionalesRead:
        self._parametros = self._parametros.model_copy(update=data.model_dump(exclude_unset=True))
        return self._parametros

    def consumir_numero_disposicion(self) -> str:
        numero = self._parametros.proxima_disposicion
        self._parametros = self._parametros.model_copy(update={"proxima_disposicion": numero + 1})
        return f"{numero}/{self._parametros.ejercicio}"


parametros_institucionales_service = ParametrosInstitucionalesService()
