# Commit 0007

## Objetivo

Impedir que el expediente saltee pasos administrativos críticos.

## Reglas

### Validar expediente

No se puede validar si existen errores críticos:

- falta expediente interno;
- falta número de disposición;
- falta establecimiento;
- falta objeto;
- falta Orden de Pago.

### Generar disposición

No se puede generar si:

- existen errores críticos;
- el expediente no está validado.

## Flujo esperado

Crear expediente → Cargar OP → Analizar OP → Ver validación → Validar expediente → Generar disposición.
