import unittest
from datetime import datetime
from types import SimpleNamespace

from app.schemas.checklist_fisico import ChecklistFisicoRead
from app.services.evidencias_documentales import obtener_evidencias_documentales


class EvidenciasDocumentalesTest(unittest.TestCase):
    def test_checklist_completo_acredita_los_cinco_requisitos(self) -> None:
        evidencias = obtener_evidencias_documentales(
            [], self._checklist(True, True, True, True, True)
        )

        self.assertTrue(all(evidencias.values()))

    def test_factura_detectada_en_op_acredita_factura(self) -> None:
        evidencias = obtener_evidencias_documentales(
            [SimpleNamespace(tipo="OP")],
            None,
            factura_detectada_en_op=True,
        )

        self.assertTrue(evidencias["factura"])
        self.assertFalse(evidencias["remito_conformidad"])

    def test_documentos_digitales_acreditan_cada_requisito(self) -> None:
        documentos = [
            SimpleNamespace(tipo=tipo)
            for tipo in (
                "FACTURA",
                "CONFORMIDAD",
                "VALIDACION_CAE",
                "ARCA",
                "ARBA",
            )
        ]

        evidencias = obtener_evidencias_documentales(documentos, None)

        self.assertTrue(all(evidencias.values()))

    def test_checklist_parcial_conserva_solo_faltantes_reales(self) -> None:
        evidencias = obtener_evidencias_documentales(
            [], self._checklist(True, True, False, True, False)
        )

        faltantes = {
            nombre
            for nombre, acreditada in evidencias.items()
            if not acreditada
        }
        self.assertEqual(faltantes, {"cae", "arba"})

    def test_sin_evidencias_no_acredita_requisitos(self) -> None:
        evidencias = obtener_evidencias_documentales([], None)

        self.assertFalse(any(evidencias.values()))

    @staticmethod
    def _checklist(
        factura: bool,
        remito: bool,
        cae: bool,
        arca: bool,
        arba: bool,
    ) -> ChecklistFisicoRead:
        return ChecklistFisicoRead(
            expediente_id="EXP-1",
            factura=factura,
            remito_conformidad=remito,
            cae=cae,
            arca=arca,
            arba=arba,
            usuario="Operador",
            fecha=datetime(2026, 8, 5),
        )


if __name__ == "__main__":
    unittest.main()
