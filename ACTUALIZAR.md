# Sprint 0021 - Consolidación y Validación Inteligente

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0021.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0021 - Consolidación y Validación Inteligente

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint consolida el flujo del expediente e incorpora validación inteligente:

- El backend aplica reglas más estrictas antes de validar.
- Si falta documentación crítica, no permite validar.
- Si hay inconsistencias económicas, no permite validar.
- La validación administrativa queda alineada con la IA documental.
- Se mejora la trazabilidad del intento de validación.
- Se prepara el terreno para generación asistida de disposición.

## Prueba recomendada

1. Crear expediente.
2. Cargar la OP de MONKE WALTER ANDRES.
3. Ejecutar IA documental.
4. Intentar validar.
5. Resultado esperado:
   - El sistema no debe validar si faltan documentos obligatorios.
   - Debe informar qué falta.
6. Cargar documentos complementarios y volver a validar.
