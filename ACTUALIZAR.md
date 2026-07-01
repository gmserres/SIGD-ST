# Sprint 0024 - Generación Asistida de Disposición

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0024.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0024 - Generación Asistida de Disposición

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint incorpora el editor inteligente de disposiciones:

- Genera un borrador editable.
- Usa estructura: VISTO, CONSIDERANDO y “EL CUERPO DE CONSEJEROS ESCOLARES DE GRAL. ALVARADO DISPONE”.
- Completa datos desde el expediente y la OP.
- Agrega observaciones IA.
- Diferencia visualmente Validado y Validado con observaciones.
- Oculta acciones que ya no corresponden según el estado del expediente.

## Prueba recomendada

1. Validar un expediente o validarlo con observaciones.
2. Ir a Resumen.
3. Presionar “Generar borrador de disposición”.
4. Revisar y editar el borrador.
5. Guardar borrador.
6. Emitir disposición.
