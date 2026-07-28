import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal

from app.domain.disposicion import Disposicion


class DisposicionDominioTest(unittest.TestCase):
    def test_construccion_valida_conserva_decimales_y_ruta(self):
        disposicion = self._crear()
        self.assertEqual(disposicion.importe, Decimal("1000.50"))
        self.assertEqual(disposicion.cantidad_uc, Decimal("0.59660"))
        self.assertEqual(
            disposicion.ruta_docx,
            "exports/EXP-1/disposicion.docx",
        )

    def test_es_inmutable(self):
        with self.assertRaises(FrozenInstanceError):
            self._crear().texto_emitido = "otro"

    def test_rechaza_campos_obligatorios_vacios(self):
        for campo in (
            "fondo_interviniente",
            "texto_emitido",
            "numero_op",
            "proveedor",
            "cuit",
        ):
            with self.subTest(campo=campo):
                datos = self._crear().__dict__ | {campo: " "}
                with self.assertRaises(ValueError):
                    Disposicion(**datos)

    def test_valida_ruta_relativa_portable(self):
        invalidas = (
            "/storage/disposicion.docx",
            "C:/storage/disposicion.docx",
            r"C:\storage\disposicion.docx",
            r"exports\disposicion.docx",
            "exports/../secreto.docx",
            "../secreto.docx",
            "exports//disposicion.docx",
        )
        for ruta in invalidas:
            with self.subTest(ruta=ruta):
                with self.assertRaises(ValueError):
                    Disposicion(
                        **(
                            self._crear().__dict__
                            | {"ruta_docx": ruta}
                        )
                    )

    @staticmethod
    def _crear() -> Disposicion:
        return Disposicion(
            id_disposicion="00000000-0000-0000-0000-000000000001",
            expediente_id="EXP-1",
            configuracion_uc_id="configuracion-1",
            numero_disposicion="1/2026",
            fecha_emision=datetime(2026, 7, 28, 10),
            fondo_interviniente="FONDO_COMPENSADOR",
            numero_op="OP-1",
            numero_liquidacion=None,
            proveedor="Proveedor",
            cuit="30-00000000-0",
            importe=Decimal("1000.50"),
            objeto="Objeto",
            establecimiento="EP 1",
            valor_uc_aplicado=Decimal("1677"),
            cantidad_uc=Decimal("0.59660"),
            procedimiento_contratacion="Factura Conformada",
            norma_uc="Ley 13.981",
            texto_emitido="VISTO\n\nCONSIDERANDO\n\nDISPONE",
            ruta_docx="exports/EXP-1/disposicion.docx",
        )
