VALOR_UC_VIGENTE = 1677
NORMA_UC = "Resolución OPC Nº 54/2025"


def calcular_uc(importe: float) -> float:
    return round(importe / VALOR_UC_VIGENTE, 2)


def determinar_procedimiento(cantidad_uc: float) -> str:
    if cantidad_uc <= 10000:
        return "Factura Conformada"
    if cantidad_uc <= 50000:
        return "Procedimiento Abreviado"
    if cantidad_uc <= 100000:
        return "Contratación Menor"
    return "Procedimiento superior a 100.000 UC"


def encuadre_legal(procedimiento: str) -> str:
    if procedimiento == "Factura Conformada":
        return "Artículo 18 inciso C de la Ley N.º 13.981, reglamentado por el Decreto N.º 59/19 y su modificatorio Decreto N.º 605/20"
    return "Encuadre legal pendiente de parametrización"
