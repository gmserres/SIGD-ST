from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class Disposicion:
    id_disposicion: str
    expediente_id: str
    configuracion_uc_id: str
    numero_disposicion: str
    fecha_emision: datetime
    fondo_interviniente: str
    numero_op: str
    numero_liquidacion: str | None
    proveedor: str
    cuit: str
    importe: Decimal
    objeto: str
    establecimiento: str
    valor_uc_aplicado: Decimal
    cantidad_uc: Decimal
    procedimiento_contratacion: str
    norma_uc: str
    texto_emitido: str
    ruta_docx: str

    def __post_init__(self) -> None:
        obligatorios = {
            "id_disposicion": self.id_disposicion,
            "expediente_id": self.expediente_id,
            "configuracion_uc_id": self.configuracion_uc_id,
            "numero_disposicion": self.numero_disposicion,
            "fondo_interviniente": self.fondo_interviniente,
            "numero_op": self.numero_op,
            "proveedor": self.proveedor,
            "cuit": self.cuit,
            "objeto": self.objeto,
            "establecimiento": self.establecimiento,
            "procedimiento_contratacion": self.procedimiento_contratacion,
            "norma_uc": self.norma_uc,
            "texto_emitido": self.texto_emitido,
            "ruta_docx": self.ruta_docx,
        }
        for nombre, valor in obligatorios.items():
            if not valor.strip():
                raise ValueError(f"{nombre} es obligatorio.")

        for nombre, valor in {
            "importe": self.importe,
            "valor_uc_aplicado": self.valor_uc_aplicado,
            "cantidad_uc": self.cantidad_uc,
        }.items():
            if not isinstance(valor, Decimal):
                raise TypeError(f"{nombre} debe ser Decimal.")

        partes_ruta = self.ruta_docx.split("/")
        ruta_windows = PureWindowsPath(self.ruta_docx)
        if (
            PurePosixPath(self.ruta_docx).is_absolute()
            or ruta_windows.is_absolute()
            or bool(ruta_windows.drive)
            or "\\" in self.ruta_docx
            or any(parte in {"", ".", ".."} for parte in partes_ruta)
        ):
            raise ValueError("ruta_docx debe ser una ruta relativa portable.")
