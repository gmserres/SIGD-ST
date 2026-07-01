# Sprint 0023 - Validación con Observaciones

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0023.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0023 - Validación con Observaciones

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint incorpora el flujo realista de validación administrativa:

- Validación normal cuando el expediente está completo.
- Validación con observaciones cuando hay advertencias no críticas.
- Motivo obligatorio para validar con observaciones.
- Registro del motivo en historial.
- Bloqueo solo ante errores críticos.

## Cómo probar

1. Crear expediente.
2. Cargar OP.
3. Ejecutar IA documental.
4. Ir a Validación.
5. Si el estado es AMARILLO, ingresar motivo y usar "Validar con observaciones".
6. Revisar Historial.
