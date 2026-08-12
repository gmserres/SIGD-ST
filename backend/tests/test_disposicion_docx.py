import asyncio
import importlib
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from app.core.settings import STORAGE_DIR
from app.services.disposicion_docx import DisposicionDocxService


async def _get_asgi(app, path: str) -> tuple[int, bytes]:
    mensajes = []
    solicitud_enviada = False

    async def receive():
        nonlocal solicitud_enviada
        if not solicitud_enviada:
            solicitud_enviada = True
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }
        return {"type": "http.disconnect"}

    async def send(mensaje):
        mensajes.append(mensaje)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("test", 123),
            "server": ("test", 80),
            "root_path": "",
        },
        receive,
        send,
    )
    estado = next(
        mensaje["status"]
        for mensaje in mensajes
        if mensaje["type"] == "http.response.start"
    )
    contenido = b"".join(
        mensaje.get("body", b"")
        for mensaje in mensajes
        if mensaje["type"] == "http.response.body"
    )
    return estado, contenido


class DisposicionDocxServiceTest(unittest.TestCase):
    def test_fastapi_publica_archivos_desde_storage_dir_configurado(self):
        contenido = b"docx persistido de prueba"
        with TemporaryDirectory() as temporal:
            raiz = Path(temporal).resolve()
            storage_dir = raiz / "storage-configurado"
            archivo = (
                storage_dir
                / "exports"
                / "EXP-TEST"
                / "disposicion.docx"
            )
            archivo.parent.mkdir(parents=True)
            archivo.write_bytes(contenido)
            otro_cwd = raiz / "otro-cwd"
            otro_cwd.mkdir()

            main_previo = sys.modules.pop("app.main", None)
            cwd_original = Path.cwd()
            try:
                with patch(
                    "app.core.settings.STORAGE_DIR",
                    storage_dir,
                ):
                    main = importlib.import_module("app.main")
                os.chdir(otro_cwd)
                estado, respuesta = asyncio.run(
                    _get_asgi(
                        main.app,
                        "/storage/exports/EXP-TEST/disposicion.docx",
                    )
                )
                estado_inexistente, _ = asyncio.run(
                    _get_asgi(
                        main.app,
                        "/storage/exports/EXP-TEST/inexistente.docx",
                    )
                )
            finally:
                os.chdir(cwd_original)
                sys.modules.pop("app.main", None)
                if main_previo is not None:
                    sys.modules["app.main"] = main_previo

            self.assertEqual(estado, 200)
            self.assertEqual(respuesta, contenido)
            self.assertEqual(estado_inexistente, 404)

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
                        "disposicion_service.obtener_exportable",
                        return_value=borrador,
                    ),
                    patch(
                        "app.services.disposicion_docx."
                        "historial_service.registrar"
                    ),
                ):
                    salida = service.generar_docx("EXP-1", "DOC-000001")
            finally:
                os.chdir(cwd_original)

            self.assertTrue(salida.is_file())
            self.assertEqual(
                salida.parent,
                export_dir.resolve() / "EXP-1" / "DOC-000001",
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
