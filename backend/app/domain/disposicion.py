from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePosixPath, PureWindowsPath

from app.domain.proveedor import normalizar_cuit


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
    documento_op_id: str | None = None
    control_proveedor_op_id: str | None = None
    seleccion_proveedor_id: str | None = None
    proveedor_definitivo_id: str | None = None
    proveedor_definitivo_cuit: str | None = None
    proveedor_definitivo_razon_social: str | None = None
    fecha_formalizacion: date | None = None
    usuario_registro_formalizacion: str | None = None
    registrado_formalizacion_en: datetime | None = None

    def __post_init__(self) -> None:
        metadatos_formalizacion = (
            self.fecha_formalizacion,
            self.usuario_registro_formalizacion,
            self.registrado_formalizacion_en,
        )
        if any(valor is None for valor in metadatos_formalizacion) and any(
            valor is not None for valor in metadatos_formalizacion
        ):
            raise ValueError(
                "Los metadatos de formalización deben estar completos."
            )
        if self.usuario_registro_formalizacion is not None:
            usuario = self.usuario_registro_formalizacion.strip()
            if not usuario:
                raise ValueError(
                    "usuario_registro_formalizacion no puede estar vacío."
                )
            object.__setattr__(
                self, "usuario_registro_formalizacion", usuario
            )
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

        for nombre in (
            "documento_op_id",
            "control_proveedor_op_id",
            "seleccion_proveedor_id",
            "proveedor_definitivo_id",
        ):
            valor = getattr(self, nombre)
            if valor is None:
                continue
            if not isinstance(valor, str):
                raise TypeError(f"{nombre} debe ser texto.")
            valor = valor.strip()
            if not valor:
                raise ValueError(f"{nombre} no puede estar vacío.")
            object.__setattr__(self, nombre, valor)

        if self.proveedor_definitivo_cuit is not None:
            object.__setattr__(
                self,
                "proveedor_definitivo_cuit",
                normalizar_cuit(self.proveedor_definitivo_cuit),
            )

        if self.proveedor_definitivo_razon_social is not None:
            if not isinstance(
                self.proveedor_definitivo_razon_social,
                str,
            ):
                raise TypeError(
                    "proveedor_definitivo_razon_social debe ser texto."
                )
            razon_social = self.proveedor_definitivo_razon_social.strip()
            if not razon_social:
                raise ValueError(
                    "proveedor_definitivo_razon_social no puede estar vacía."
                )
            object.__setattr__(
                self,
                "proveedor_definitivo_razon_social",
                razon_social,
            )

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
