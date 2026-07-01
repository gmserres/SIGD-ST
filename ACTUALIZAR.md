# Sprint 0025 - Checklist Físico en Validación

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0025.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0025 - Checklist Físico en Validación

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint incorpora el checklist físico dentro de la etapa de validación:

- La validación muestra los faltantes.
- Desde Validación se puede abrir "Acreditar documentación física".
- El operador marca qué documentación obra físicamente en el expediente.
- El checklist queda registrado en historial.
- La validación se recalcula y puede pasar de AMARILLO a VERDE.
- Si el checklist completa las evidencias, el expediente puede salir validado sin observaciones.
- Se corrige el mensaje persistente al cambiar de expediente/estado.

## Prueba recomendada

1. Crear expediente.
2. Cargar OP.
3. Ejecutar IA documental.
4. Ir a Validación.
5. Presionar "Acreditar documentación física".
6. Marcar Remito/Conformidad, CAE, ARCA y ARBA.
7. Guardar checklist.
8. Volver a validar: debería quedar VERDE si no hay otros faltantes.
