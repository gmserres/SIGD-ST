# Prueba manual - Commit 0007

## Caso 1: validar sin OP

1. Crear expediente.
2. No cargar OP.
3. Presionar Validar expediente.

Resultado esperado:
- No cambia a VALIDADO.
- Muestra error.
- Registra VALIDACION_BLOQUEADA.

## Caso 2: generar disposición sin OP

1. Crear expediente.
2. No cargar OP.
3. Presionar Generar disposición.

Resultado esperado:
- No cambia a DISPOSICION_EMITIDA.
- Muestra error.
- Registra GENERACION_DISPOSICION_BLOQUEADA.

## Caso 3: flujo correcto

1. Crear expediente.
2. Cargar OP.
3. Ver validación.
4. Validar expediente.
5. Generar disposición.

Resultado esperado:
- Cambia a VALIDADO.
- Luego cambia a DISPOSICION_EMITIDA.
