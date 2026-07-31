# Catálogo de variables - Plantilla FC 2026

La plantilla oficial de Fondo Compensador se encuentra en `storage/templates/disposicion_fc_v2026.md`.
El archivo Word base corregido se conserva en `storage/templates/DISPOSICION_OFICIAL_FC_2026_BASE.docx`.

## Variables principales

| Variable | Origen |
|---|---|
| `{{FECHA}}` | Sistema / fecha de emisión |
| `{{EXPEDIENTE}}` | Expediente |
| `{{DISPOSICION}}` | Expediente / numeración |
| `{{PROVEEDOR}}` | OP |
| `{{CUIT}}` | OP |
| `{{IMPORTE}}` | OP - Monto total de facturas |
| `{{IMPORTE_LETRAS}}` | Calculado |
| `{{UC}}` | Calculado: importe / valor de la Configuración UC aplicada al Expediente |
| `{{NORMA_UC}}` | Configuración UC vigente o histórica asociada al Expediente |
| `{{TABLA_FACTURAS}}` | OP - facturas liquidadas |
| `{{CONCEPTO_PAGO}}` | Expediente / objeto |
| `{{ESTABLECIMIENTOS}}` | Expediente |
| `{{PROCEDIMIENTO}}` | Rango aplicable de la Configuración UC vigente o histórica asociada al Expediente |
| `{{ARTICULO_DR}}` | Motor normativo inicial |
| `{{TABLA_DETALLE_OP}}` | OP - retenciones, neto, forma de pago y CBU |
| `{{FONDO}}` | OP |
| `{{EJERCICIO}}` | Parámetros institucionales |

## Decisiones de diseño

- La disposición no se redacta libremente: se completa una plantilla oficial.
- La OP es la fuente principal de datos económicos.
- El valor UC y la norma UC provienen de la Configuración UC vigente o histórica
  asociada al Expediente; el procedimiento proviene del rango aplicable de esa
  configuración.
- El detalle económico del Artículo 2° se presenta como tabla alineada.
- Las retenciones son informativas y provienen de la OP.
