import unittest
from datetime import datetime
from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.api.expedientes import (
    cargar_op,
    listar_documentos,
    subir_documento,
)
from app.domain.estados import EstadoExpediente
from app.infrastructure.database.base import Base
from app.infrastructure.database.mappers.documento_mapper import (
    a_modelo,
    a_schema,
)
from app.infrastructure.database.models.expediente_model import (
    ExpedienteModel,
)
from app.infrastructure.database.repositories.documento_postgres_repository import (
    PostgresDocumentoRepository,
)
from app.schemas.documento import DocumentoCreate, DocumentoRead
from app.services.documentos import DocumentoService


class DocumentoPersistenciaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:"
        )
        with self.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )
        self._guardar_expediente("EXP-1")

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_mapper_conserva_todos_los_campos(self) -> None:
        data = self._data()
        fecha_carga = datetime(2026, 7, 29, 10)
        modelo = a_modelo("EXP-1", data, fecha_carga)
        modelo.secuencia = 1

        self.assertEqual(
            a_schema(modelo),
            DocumentoRead(
                id="DOC-000001",
                expediente_id="EXP-1",
                fecha_carga=fecha_carga,
                **data.model_dump(),
            ),
        )

    def test_persiste_y_recupera_desde_nueva_instancia(self) -> None:
        repository = PostgresDocumentoRepository(self.factory)
        documento = repository.guardar(
            "EXP-1",
            self._data(),
            datetime(2026, 7, 29, 10),
        )

        reconstruido = PostgresDocumentoRepository(self.factory)

        self.assertEqual(
            reconstruido.obtener("EXP-1", documento.id),
            documento,
        )

    def test_lista_con_orden_determinista(self) -> None:
        repository = PostgresDocumentoRepository(self.factory)
        posterior = repository.guardar(
            "EXP-1",
            self._data(nombre_archivo="posterior.pdf"),
            datetime(2026, 7, 29, 11),
        )
        primero = repository.guardar(
            "EXP-1",
            self._data(nombre_archivo="primero.pdf"),
            datetime(2026, 7, 29, 10),
        )
        segundo = repository.guardar(
            "EXP-1",
            self._data(nombre_archivo="segundo.pdf"),
            datetime(2026, 7, 29, 10),
        )

        self.assertEqual(
            repository.listar_por_expediente("EXP-1"),
            [primero, segundo, posterior],
        )

    def test_op_sobrevive_a_recreacion_del_servicio(self) -> None:
        repository = PostgresDocumentoRepository(self.factory)
        creada = repository.guardar(
            "EXP-1",
            self._data(
                tipo="OP",
                nombre_archivo="op.pdf",
            ),
            datetime(2026, 7, 29, 10),
        )

        reconstruido = DocumentoService(
            PostgresDocumentoRepository(self.factory)
        )
        recuperadas = reconstruido.listar_por_expediente(
            "EXP-1"
        )

        self.assertEqual(recuperadas, [creada])
        self.assertEqual(recuperadas[0].tipo, "OP")

    def test_servicio_conserva_formato_del_identificador(self) -> None:
        servicio = DocumentoService(
            PostgresDocumentoRepository(self.factory)
        )

        creado = servicio.agregar("EXP-1", self._data())

        self.assertEqual(creado.id, "DOC-000001")

    def test_rechaza_expediente_inexistente(self) -> None:
        repository = PostgresDocumentoRepository(self.factory)

        with self.assertRaises(IntegrityError):
            repository.guardar(
                "EXP-INEXISTENTE",
                self._data(),
                datetime(2026, 7, 29, 10),
            )

    def _guardar_expediente(self, expediente_id: str) -> None:
        with self.factory() as session:
            session.add(
                ExpedienteModel(
                    id=expediente_id,
                    numero_interno="033-074/2026",
                    numero_gdeba="EX-2026-0074-SIGDST",
                    solicitud_intervencion_id=None,
                    decision_administrativa_id=None,
                    configuracion_uc_id=None,
                    id_suna=None,
                    tipo_tramite="FONDO_COMPENSADOR",
                    estado=EstadoExpediente.VALIDADO.value,
                    establecimiento="EP 74",
                    objeto="Objeto",
                    numero_disposicion=None,
                    creado=datetime(2026, 7, 29, 9),
                )
            )
            session.commit()

    @staticmethod
    def _data(
        *,
        tipo: str = "FACTURA",
        nombre_archivo: str = "factura.pdf",
    ) -> DocumentoCreate:
        return DocumentoCreate(
            tipo=tipo,
            nombre_archivo=nombre_archivo,
            ruta=(
                "storage/expedientes/EXP-1/"
                f"{nombre_archivo}"
            ),
            observaciones=None,
            tamano_bytes=100,
            mime_type="application/pdf",
        )


class DocumentoEndpointTest(unittest.IsolatedAsyncioTestCase):
    async def test_upload_conserva_contrato_actual(self) -> None:
        esperado = DocumentoRead(
            id="DOC-000001",
            expediente_id="EXP-1",
            tipo="FACTURA",
            nombre_archivo="factura.pdf",
            ruta="storage/expedientes/EXP-1/factura.pdf",
            fecha_carga=datetime(2026, 7, 29, 10),
            observaciones="Observación",
            tamano_bytes=100,
            mime_type="application/pdf",
        )
        archivo = UploadFile(
            filename="factura.pdf",
            file=BytesIO(b"PDF"),
        )

        with (
            patch(
                "app.api.expedientes.obtener_expediente"
            ),
            patch(
                "app.api.expedientes.guardar_upload",
                new=AsyncMock(
                    return_value=(
                        esperado.nombre_archivo,
                        esperado.ruta,
                        esperado.tamano_bytes,
                        esperado.mime_type,
                    )
                ),
            ),
            patch(
                "app.api.expedientes.documento_service.agregar",
                return_value=esperado,
            ),
            patch(
                "app.api.expedientes.historial_service.registrar"
            ),
        ):
            resultado = await subir_documento(
                "EXP-1",
                "FACTURA",
                "Observación",
                archivo,
            )

        self.assertEqual(resultado, esperado)

    async def test_op_inexistente_devuelve_404_controlado(
        self,
    ) -> None:
        archivo = UploadFile(
            filename="op.pdf",
            file=BytesIO(b"PDF"),
        )

        with patch(
            "app.api.expedientes.obtener_expediente",
            side_effect=HTTPException(
                status_code=404,
                detail="Expediente no encontrado",
            ),
        ):
            with self.assertRaises(HTTPException) as contexto:
                await cargar_op("EXP-INEXISTENTE", archivo)

        self.assertEqual(contexto.exception.status_code, 404)

    async def test_op_elimina_archivo_si_falla_operacion_coordinada(
        self,
    ) -> None:
        archivo = UploadFile(
            filename="op.pdf",
            file=BytesIO(b"PDF"),
        )
        with (
            patch("app.api.expedientes.obtener_expediente"),
            patch(
                "app.api.expedientes.guardar_upload",
                new=AsyncMock(
                    return_value=(
                        "op.pdf",
                        "storage/expedientes/EXP-1/op.pdf",
                        100,
                        "application/pdf",
                    )
                ),
            ),
            patch(
                "app.api.expedientes.documento_service.agregar_op",
                side_effect=RuntimeError("Fallo de base"),
            ),
            patch(
                "app.api.expedientes._eliminar_archivo_guardado"
            ) as eliminar,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Fallo de base",
            ):
                await cargar_op("EXP-1", archivo)

        eliminar.assert_called_once_with(
            "storage/expedientes/EXP-1/op.pdf"
        )

    async def test_elimina_archivo_si_falla_persistencia(
        self,
    ) -> None:
        archivo = UploadFile(
            filename="factura.pdf",
            file=BytesIO(b"PDF"),
        )

        with (
            patch(
                "app.api.expedientes.obtener_expediente"
            ),
            patch(
                "app.api.expedientes.guardar_upload",
                new=AsyncMock(
                    return_value=(
                        "factura.pdf",
                        "storage/expedientes/EXP-1/factura.pdf",
                        100,
                        "application/pdf",
                    )
                ),
            ),
            patch(
                "app.api.expedientes.documento_service.agregar",
                side_effect=RuntimeError("Error controlado"),
            ),
            patch(
                "app.api.expedientes._eliminar_archivo_guardado"
            ) as eliminar,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Error controlado",
            ):
                await subir_documento(
                    "EXP-1",
                    "FACTURA",
                    None,
                    archivo,
                )

        eliminar.assert_called_once_with(
            "storage/expedientes/EXP-1/factura.pdf"
        )

    def test_listado_conserva_respuesta_documental(self) -> None:
        esperado = [
            DocumentoRead(
                id="DOC-000001",
                expediente_id="EXP-1",
                tipo="OP",
                nombre_archivo="op.pdf",
                ruta="storage/expedientes/EXP-1/op.pdf",
                fecha_carga=datetime(2026, 7, 29, 10),
                observaciones=None,
                tamano_bytes=100,
                mime_type="application/pdf",
            )
        ]

        with (
            patch(
                "app.api.expedientes.obtener_expediente"
            ),
            patch(
                "app.api.expedientes.documento_service."
                "listar_por_expediente",
                return_value=esperado,
            ),
        ):
            resultado = listar_documentos("EXP-1")

        self.assertEqual(resultado, esperado)


if __name__ == "__main__":
    unittest.main()
