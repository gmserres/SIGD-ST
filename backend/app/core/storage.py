from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage" / "expedientes"


def asegurar_carpeta_expediente(expediente_id: str) -> Path:
    carpeta = STORAGE_ROOT / expediente_id
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def nombre_seguro(nombre: str) -> str:
    reemplazos = {
        " ": "_",
        "/": "-",
        "\\": "-",
        ":": "-",
        "*": "",
        "?": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "",
    }
    limpio = nombre.strip()
    for origen, destino in reemplazos.items():
        limpio = limpio.replace(origen, destino)
    return limpio or "documento"


async def guardar_upload(expediente_id: str, archivo: UploadFile, prefijo: str) -> tuple[str, str, int, str | None]:
    carpeta = asegurar_carpeta_expediente(expediente_id)
    nombre_original = archivo.filename or "documento.pdf"
    nombre_final = f"{prefijo}_{uuid4().hex[:8]}_{nombre_seguro(nombre_original)}"
    destino = carpeta / nombre_final

    contenido = await archivo.read()
    destino.write_bytes(contenido)

    ruta_relativa = destino.relative_to(Path(__file__).resolve().parents[3]).as_posix()
    return nombre_original, ruta_relativa, len(contenido), archivo.content_type
