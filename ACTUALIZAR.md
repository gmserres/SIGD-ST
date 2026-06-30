# Sprint 0019 - Asistente Inteligente del Expediente

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0019.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0019 - Asistente Inteligente del Expediente

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint agrega la primera versión del asistente inteligente del expediente:

- Corrige la extracción de proveedor para OP tipo MONKE.
- Agrega diagnóstico automático del expediente en IA documental.
- Agrega semáforo documental: Verde, Amarillo o Rojo.
- Agrega porcentaje de avance documental.
- Agrega checklist inteligente.
- Mejora la recomendación administrativa del sistema.

## Prueba recomendada

1. Crear expediente.
2. Cargar la OP de MONKE WALTER ANDRES.
3. Ejecutar IA documental.
4. Verificar que detecte:
   - Proveedor: MONKE WALTER ANDRES.
   - CUIT: 20-16898364-7.
   - Bruto: $840.000,00.
   - Neto: $706.140,03.
   - 6 facturas.
   - 3 retenciones.
5. Revisar el nuevo panel "Diagnóstico del expediente".
