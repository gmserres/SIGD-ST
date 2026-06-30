# Sprint 0021 - Consolidación y Validación Inteligente

## Objetivo

Evitar que el expediente avance cuando la IA y las validaciones detectan faltantes o inconsistencias relevantes.

## Reglas principales

No permite validar si:

- no existe OP;
- no hay proveedor detectable;
- no hay CUIT detectable;
- no hay importe;
- no hay facturas liquidadas;
- la suma de facturas no coincide con la OP;
- faltan documentos obligatorios mínimos.

## Documentos considerados obligatorios en esta etapa

- OP.
- Factura o facturas liquidadas.
- Remito o conformidad.
- Validación CAE.
- ARBA.
- ARCA.

## Resultado esperado

El sistema debe guiar al usuario y no permitir avances prematuros.

## Próximo sprint

Sprint 0022:

- Generación asistida de disposición.
- Borrador editable.
- Exportación inicial.
