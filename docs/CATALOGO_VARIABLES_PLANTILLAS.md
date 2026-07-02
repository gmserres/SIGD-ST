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
| `{{UC}}` | Calculado: importe / valor UC vigente |
| `{{NORMA_UC}}` | Parámetro anual del sistema |
| `{{TABLA_FACTURAS}}` | OP - facturas liquidadas |
| `{{CONCEPTO_PAGO}}` | Expediente / objeto |
| `{{ESTABLECIMIENTOS}}` | Expediente |
| `{{PROCEDIMIENTO}}` | Motor Fondo Compensador |
| `{{ARTICULO_DR}}` | Motor normativo inicial |
| `{{TABLA_DETALLE_OP}}` | OP - retenciones, neto, forma de pago y CBU |
| `{{FONDO}}` | OP |
| `{{EJERCICIO}}` | Parámetro anual / fecha OP |

## Decisiones de diseño

- La disposición no se redacta libremente: se completa una plantilla oficial.
- La OP es la fuente principal de datos económicos.
- Valor UC y norma UC son parámetros anuales.
- El detalle económico del Artículo 2° se presenta como tabla alineada.
- Las retenciones son informativas y provienen de la OP.
