import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from app.core.settings import STORAGE_DIR
from app.services.disposicion_docx import DisposicionDocxService


class DisposicionDocxServiceTest(unittest.TestCase):
    def test_genera_dentro_de_carpeta_inyectada_sin_depender_del_cwd(self):
        with TemporaryDirectory() as temporal:
            raiz = Path(temporal).resolve()
            export_dir = raiz / "storage-configurado" / "exports"
            otro_cwd = raiz / "otro-cwd"
            otro_cwd.mkdir()
            service = DisposicionDocxService(export_dir)
            expediente = SimpleNamespace(
                numero_disposicion="75/2026",
                numero_interno="033-075/2026",
            )
            borrador = SimpleNamespace(
                visto="VISTO",
                considerando="CONSIDERANDO",
                dispone="DISPONE",
            )
            cwd_original = Path.cwd()
            try:
                os.chdir(otro_cwd)
                with (
                    patch(
                        "app.services.disposicion_docx."
                        "expediente_service.obtener",
                        return_value=expediente,
                    ),
                    patch(
                        "app.services.disposicion_docx."
                        "disposicion_service.obtener",
                        return_value=borrador,
                    ),
                    patch(
                        "app.services.disposicion_docx."
                        "historial_service.registrar"
                    ),
                ):
                    salida = service.generar_docx("EXP-1")
            finally:
                os.chdir(cwd_original)

            self.assertTrue(salida.is_file())
            self.assertEqual(
                salida.parent,
                export_dir.resolve() / "EXP-1",
            )
            self.assertEqual(
                salida.name,
                "DISPOSICION_75_2026.docx",
            )

    def test_composicion_usa_unica_raiz_configurada(self):
        from app.composition.disposicion import (
            disposicion_docx_service,
        )

        self.assertEqual(
            disposicion_docx_service._export_dir,
            (STORAGE_DIR / "exports").resolve(),
        )
