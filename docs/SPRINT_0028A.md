# Sprint 0028A - Motor de Plantillas Institucionales

## Objetivo

Dejar de generar la disposición desde texto hardcodeado y comenzar a completarla desde una plantilla oficial parametrizada.

## Archivos incorporados

- `backend/app/services/template_engine.py`
- `storage/templates/disposicion_fc_v2026.md`
- `storage/templates/DISPOSICION_OFICIAL_FC_2026_BASE.docx`
- `docs/CATALOGO_VARIABLES_PLANTILLAS.md`

## Variables implementadas

- Fecha.
- Expediente.
- Disposición.
- Proveedor.
- CUIT.
- Importe.
- Importe en letras.
- UC.
- Norma UC.
- Facturas.
- Concepto de pago.
- Establecimientos.
- Procedimiento.
- Artículo DR.
- Detalle económico OP.
- Fondo.
- Ejercicio.

## Próximo sprint

Sprint 0028B:

- Exportación DOCX real basada en plantilla Word.
- Respeto de negritas y estilos del modelo oficial.
- Tablas Word nativas.
- Vista previa más fiel al documento institucional.
