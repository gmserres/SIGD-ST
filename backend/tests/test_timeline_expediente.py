from datetime import date, datetime
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.api.expedientes import listar_timeline_expediente
from app.repositories.timeline_expediente_repository import (
    FuentesTimelineExpediente,
)
from app.services.historial import HistorialService
from app.services.timeline_expediente import TimelineExpedienteService


def ns(**valores):
    return SimpleNamespace(**valores)


class RepositorioTimelineFake:
    def __init__(self, fuentes_por_expediente):
        self.fuentes_por_expediente = fuentes_por_expediente

    def obtener_fuentes(self, expediente_id):
        return self.fuentes_por_expediente.get(expediente_id)


class TimelineExpedienteTest(TestCase):
    def _fuentes(self, expediente_id="EXP-A", **cambios):
        expediente = ns(
            id=expediente_id,
            numero_interno=f"{expediente_id}/2026",
            creado=datetime(2026, 8, 1, 9, 0),
            fecha_firma=None,
            usuario_registro_firma=None,
            fecha_archivo=None,
            usuario_registro_archivo=None,
            fecha_cierre=None,
            usuario_registro_cierre=None,
            registrado_cierre_en=None,
            fecha_desistimiento=None,
            usuario_registro_desistimiento=None,
            registrado_desistimiento_en=None,
            motivo_desistimiento=None,
        )
        valores = {
            "expediente": expediente,
            "documentos": [],
            "checklist": None,
            "validaciones": [],
            "selecciones": [],
            "controles": [],
            "disposiciones": [],
        }
        valores.update(cambios)
        return FuentesTimelineExpediente(**valores)

    def _servicio(self, *fuentes):
        return TimelineExpedienteService(
            RepositorioTimelineFake(
                {fuente.expediente.id: fuente for fuente in fuentes}
            )
        )

    def test_reconstruye_fuentes_autoritativas_y_varias_op(self) -> None:
        fuentes = self._fuentes(
            documentos=[
                ns(
                    secuencia=1,
                    tipo="ACTA",
                    nombre_archivo="acta.pdf",
                    fecha_carga=datetime(2026, 8, 1, 10, 0),
                ),
                ns(
                    secuencia=2,
                    tipo="OP",
                    nombre_archivo="op-a.pdf",
                    fecha_carga=datetime(2026, 8, 2, 10, 0),
                ),
                ns(
                    secuencia=3,
                    tipo="OP",
                    nombre_archivo="op-b.pdf",
                    fecha_carga=datetime(2026, 8, 2, 11, 0),
                ),
            ],
            checklist=ns(
                id=8,
                fecha_registro=datetime(2026, 8, 1, 11, 0),
                observaciones="Documentación completa",
                usuario="secretaria",
                factura=True,
                remito_conformidad=True,
                cae=True,
                arca=True,
                arba=True,
            ),
            validaciones=[
                ns(
                    id=9,
                    fecha_validacion=datetime(2026, 8, 1, 12, 0),
                    resultado="VALIDADA_CON_OBSERVACIONES",
                    motivo_observacion="Revisar original",
                    usuario="validadora",
                    fecha_invalidacion=None,
                    motivo_invalidacion=None,
                    usuario_invalidacion=None,
                )
            ],
            selecciones=[
                ns(
                    id_seleccion="SEL-A",
                    fecha_seleccion=datetime(2026, 8, 1, 13, 0),
                    motivo_reemplazo=None,
                    proveedor_id="PROV-A",
                    proveedor_cuit="30111111118",
                    proveedor_razon_social="Proveedor A",
                    vigente=False,
                    seleccionado_por="operadora",
                ),
                ns(
                    id_seleccion="SEL-C",
                    fecha_seleccion=datetime(2026, 8, 1, 14, 0),
                    motivo_reemplazo="Cambio administrativo",
                    proveedor_id="PROV-C",
                    proveedor_cuit="30222222225",
                    proveedor_razon_social="Proveedor C",
                    vigente=True,
                    seleccionado_por="operadora",
                ),
            ],
            controles=[
                self._control("CTRL-A", 1, 2, "COINCIDE"),
                self._control("CTRL-B", 2, 3, "CUIT_DIFERENTE"),
            ],
            disposiciones=[
                self._disposicion("DISP-A", 2, "101/2026", 16, True),
                self._disposicion("DISP-B", 3, "102/2026", 17, False),
            ],
        )

        eventos = self._servicio(fuentes).obtener("EXP-A")

        tipos = [evento.tipo for evento in eventos]
        self.assertIn("CHECKLIST_FISICO_REGISTRADO", tipos)
        self.assertIn("VALIDACION_ADMINISTRATIVA", tipos)
        self.assertIn("PROVEEDOR_SELECCIONADO", tipos)
        self.assertIn("PROVEEDOR_REEMPLAZADO", tipos)
        controles = [
            evento
            for evento in eventos
            if evento.tipo == "CONTROL_PROVEEDOR_OP"
        ]
        self.assertEqual(
            [evento.documento_op_id for evento in controles],
            ["DOC-000002", "DOC-000003"],
        )
        emisiones = [
            evento
            for evento in eventos
            if evento.tipo == "DISPOSICION_EMITIDA"
        ]
        self.assertEqual(
            [evento.documento_op_id for evento in emisiones],
            ["DOC-000002", "DOC-000003"],
        )
        self.assertEqual(tipos.count("DISPOSICION_FORMALIZADA"), 1)
        reemplazo = next(
            evento
            for evento in eventos
            if evento.tipo == "PROVEEDOR_REEMPLAZADO"
        )
        self.assertEqual(
            reemplazo.metadatos["proveedor_anterior"], "Proveedor A"
        )
        self.assertIn("Cambio administrativo", reemplazo.descripcion)

    def test_historial_vacio_no_modifica_timeline(self) -> None:
        fuentes = self._fuentes(
            checklist=ns(
                id=1,
                fecha_registro=datetime(2026, 8, 2, 10),
                observaciones=None,
                usuario="usuario",
                factura=True,
                remito_conformidad=True,
                cae=True,
                arca=True,
                arba=True,
            )
        )
        servicio = self._servicio(fuentes)
        historial = HistorialService()
        historial.registrar("EXP-A", "EVENTO_EFIMERO")
        antes = servicio.obtener("EXP-A")
        historial = HistorialService()
        self.assertEqual(historial.listar_por_expediente("EXP-A"), [])
        despues = servicio.obtener("EXP-A")
        self.assertEqual(antes, despues)

    def test_orden_determinista_en_empates(self) -> None:
        instante = datetime(2026, 8, 2, 10)
        fuentes = self._fuentes(
            documentos=[
                ns(
                    secuencia=2,
                    tipo="OP",
                    nombre_archivo="op.pdf",
                    fecha_carga=instante,
                )
            ],
            checklist=ns(
                id=1,
                fecha_registro=instante,
                observaciones=None,
                usuario="usuario",
                factura=True,
                remito_conformidad=True,
                cae=True,
                arca=True,
                arba=True,
            ),
        )
        servicio = self._servicio(fuentes)
        primero = servicio.obtener("EXP-A")
        segundo = servicio.obtener("EXP-A")
        self.assertEqual(primero, segundo)
        self.assertLess(
            [e.tipo for e in primero].index("OP_INCORPORADA"),
            [e.tipo for e in primero].index(
                "CHECKLIST_FISICO_REGISTRADO"
            ),
        )

    def test_expedientes_de_misma_solicitud_quedan_aislados(self) -> None:
        fuentes_a = self._fuentes(
            "EXP-A",
            documentos=[
                ns(
                    secuencia=2,
                    tipo="OP",
                    nombre_archivo="a.pdf",
                    fecha_carga=datetime(2026, 8, 2, 10),
                )
            ],
        )
        fuentes_b = self._fuentes("EXP-B")
        servicio = self._servicio(fuentes_a, fuentes_b)
        self.assertTrue(
            any(e.tipo == "OP_INCORPORADA" for e in servicio.obtener("EXP-A"))
        )
        self.assertFalse(
            any(e.tipo == "OP_INCORPORADA" for e in servicio.obtener("EXP-B"))
        )

    def test_desistimiento_y_archivo_preservan_motivo_y_procedencia(
        self,
    ) -> None:
        fuentes = self._fuentes()
        fuentes.expediente.fecha_desistimiento = date(2026, 8, 5)
        fuentes.expediente.registrado_desistimiento_en = datetime(
            2026, 8, 5, 12
        )
        fuentes.expediente.usuario_registro_desistimiento = "operadora"
        fuentes.expediente.motivo_desistimiento = "Sin ejecución"
        fuentes.expediente.fecha_archivo = date(2026, 8, 5)
        fuentes.expediente.usuario_registro_archivo = "sistema"
        eventos = self._servicio(fuentes).obtener("EXP-A")
        desistimiento = next(
            e for e in eventos if e.tipo == "EXPEDIENTE_DESISTIDO"
        )
        archivo = next(
            e for e in eventos if e.tipo == "EXPEDIENTE_ARCHIVADO"
        )
        self.assertEqual(desistimiento.descripcion, "Sin ejecución")
        self.assertEqual(archivo.metadatos["procedencia"], "DESISTIDO")
        self.assertLess(eventos.index(desistimiento), eventos.index(archivo))

    def test_cierre_y_archivo_conservan_orden_en_mismo_dia(self) -> None:
        fuentes = self._fuentes()
        fuentes.expediente.fecha_cierre = date(2026, 8, 5)
        fuentes.expediente.registrado_cierre_en = datetime(2026, 8, 5, 18)
        fuentes.expediente.usuario_registro_cierre = "operadora"
        fuentes.expediente.fecha_archivo = date(2026, 8, 5)
        fuentes.expediente.usuario_registro_archivo = "sistema"
        eventos = self._servicio(fuentes).obtener("EXP-A")
        tipos = [e.tipo for e in eventos]
        self.assertLess(
            tipos.index("EXPEDIENTE_CERRADO"),
            tipos.index("EXPEDIENTE_ARCHIVADO"),
        )

    def test_archivo_legacy_no_infiere_finalizacion(self) -> None:
        fuentes = self._fuentes()
        fuentes.expediente.fecha_archivo = date(2026, 8, 5)
        fuentes.expediente.usuario_registro_archivo = "legacy"
        eventos = self._servicio(fuentes).obtener("EXP-A")
        tipos = [e.tipo for e in eventos]
        self.assertNotIn("EXPEDIENTE_CERRADO", tipos)
        self.assertNotIn("EXPEDIENTE_DESISTIDO", tipos)
        archivo = next(e for e in eventos if e.tipo == "EXPEDIENTE_ARCHIVADO")
        self.assertEqual(
            archivo.metadatos["procedencia"], "LEGACY_NO_DETERMINADA"
        )

    def test_endpoint_no_consulta_historial_service(self) -> None:
        esperado = [object()]
        with (
            patch(
                "app.api.expedientes.obtener_expediente",
                return_value=object(),
            ),
            patch(
                "app.api.expedientes.timeline_expediente_service.obtener",
                return_value=esperado,
            ) as obtener,
            patch(
                "app.api.expedientes.historial_service."
                "listar_por_expediente",
                side_effect=AssertionError("No debe consultar historial"),
            ),
        ):
            resultado = listar_timeline_expediente("EXP-A")
        self.assertIs(resultado, esperado)
        obtener.assert_called_once_with("EXP-A")

    @staticmethod
    def _control(id_control, secuencia, documento, estado):
        return ns(
            id_control=id_control,
            secuencia=secuencia,
            documento_secuencia=documento,
            fecha_control=datetime(2026, 8, 3, 10 + secuencia),
            estado=estado,
            proveedor_razon_social_seleccionada="Proveedor C",
            razon_social_detectada="Proveedor C",
            seleccion_proveedor_id="SEL-C",
            proveedor_cuit_seleccionado="30222222225",
            cuit_detectado="30222222225",
        )

    @staticmethod
    def _disposicion(id_disposicion, documento, numero, dia, formalizada):
        return ns(
            id_disposicion=id_disposicion,
            documento_op_secuencia=documento,
            fecha_emision=datetime(2026, 8, dia, 10),
            numero_disposicion=numero,
            proveedor="Proveedor C",
            numero_op=f"OP-{documento}",
            registrado_formalizacion_en=(
                datetime(2026, 8, dia + 1, 10) if formalizada else None
            ),
            usuario_registro_formalizacion=(
                "secretaria" if formalizada else None
            ),
        )
