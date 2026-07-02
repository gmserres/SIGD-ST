
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RenderResult:
    contenido: str
    variables_usadas: list[str]
    variables_faltantes: list[str]


class TemplateEngine:
    patron_variable = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")

    def cargar(self, ruta: Path) -> str:
        return ruta.read_text(encoding="utf-8")

    def variables(self, plantilla: str) -> list[str]:
        return sorted(set(self.patron_variable.findall(plantilla)))

    def renderizar(self, plantilla: str, variables: dict[str, Any]) -> RenderResult:
        usadas = self.variables(plantilla)
        faltantes: list[str] = []

        def reemplazar(match: re.Match[str]) -> str:
            nombre = match.group(1)
            valor = variables.get(nombre)
            if valor is None or valor == "":
                faltantes.append(nombre)
                return f"{{{{{nombre}}}}}"
            return str(valor)

        contenido = self.patron_variable.sub(reemplazar, plantilla)
        return RenderResult(
            contenido=contenido,
            variables_usadas=usadas,
            variables_faltantes=sorted(set(faltantes)),
        )


def formatear_moneda(valor: float | None) -> str:
    if valor is None:
        return "importe pendiente de verificación"
    entero, decimales = f"{valor:.2f}".split(".")
    partes: list[str] = []
    while entero:
        partes.insert(0, entero[-3:])
        entero = entero[:-3]
    return "$" + ".".join(partes) + "," + decimales


def formatear_numero(valor: float | None, decimales: int = 2) -> str:
    if valor is None:
        return "-"
    entero, decimal = f"{valor:.{decimales}f}".split(".")
    partes: list[str] = []
    while entero:
        partes.insert(0, entero[-3:])
        entero = entero[:-3]
    return ".".join(partes) + "," + decimal


_UNIDADES = [
    "", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
    "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE",
]
_DECENAS = ["", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
_CENTENAS = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]


def _menor_mil(n: int) -> str:
    if n == 0:
        return ""
    if n == 100:
        return "CIEN"
    if n < 20:
        return _UNIDADES[n]
    if n < 30:
        if n == 20:
            return "VEINTE"
        return "VEINTI" + _UNIDADES[n - 20].lower().upper()
    if n < 100:
        decena = n // 10
        unidad = n % 10
        if unidad == 0:
            return _DECENAS[decena]
        return f"{_DECENAS[decena]} Y {_UNIDADES[unidad]}"
    centena = n // 100
    resto = n % 100
    texto = _CENTENAS[centena]
    if resto:
        texto += " " + _menor_mil(resto)
    return texto


def numero_a_letras(valor: float | None) -> str:
    if valor is None:
        return "IMPORTE PENDIENTE DE VERIFICACIÓN"
    pesos = int(valor)
    centavos = int(round((valor - pesos) * 100))

    if pesos == 0:
        texto = "CERO"
    elif pesos < 1000:
        texto = _menor_mil(pesos)
    elif pesos < 1_000_000:
        miles = pesos // 1000
        resto = pesos % 1000
        if miles == 1:
            texto = "MIL"
        else:
            texto = _menor_mil(miles) + " MIL"
        if resto:
            texto += " " + _menor_mil(resto)
    else:
        millones = pesos // 1_000_000
        resto = pesos % 1_000_000
        texto = ("UN MILLÓN" if millones == 1 else _menor_mil(millones) + " MILLONES")
        if resto:
            if resto < 1000:
                texto += " " + _menor_mil(resto)
            else:
                miles = resto // 1000
                ult = resto % 1000
                texto += " " + (_menor_mil(miles) + " MIL" if miles > 1 else "MIL")
                if ult:
                    texto += " " + _menor_mil(ult)
    return f"{texto} CON {centavos:02d}/100"


def dividir_disposicion(contenido: str) -> tuple[str, str, str]:
    """Divide el documento renderizado para mantener compatibilidad con el editor actual."""
    considerando_idx = contenido.find("CONSIDERANDO:")
    dispone_idx = contenido.find("DISPONE")

    if considerando_idx == -1 or dispone_idx == -1:
        return contenido, "", ""

    visto = contenido[:considerando_idx].strip()
    considerando = contenido[considerando_idx:dispone_idx].strip()
    dispone = contenido[dispone_idx:].strip()
    return visto, considerando, dispone


template_engine = TemplateEngine()
