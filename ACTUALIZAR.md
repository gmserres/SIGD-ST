# Sprint 0028A - Motor de Plantillas Institucionales

## Cómo actualizar

1. Descomprimir `SIGD-ST_sprint_0028A.zip`.
2. Copiar todo el contenido dentro del repositorio `SIGD-ST`.
3. Reemplazar archivos cuando Windows lo pregunte.
4. En GitHub Desktop usar este Summary:

Sprint 0028A - Motor de Plantillas Institucionales

5. Commit to main.
6. Push origin.
7. Reiniciar backend y frontend.

## Resultado

Este sprint reemplaza la disposición hardcodeada por un motor inicial de plantillas:

- Nuevo servicio `template_engine`.
- Plantilla parametrizada `storage/templates/disposicion_fc_v2026.md`.
- Se conserva el Word oficial corregido como base en `storage/templates/DISPOSICION_OFICIAL_FC_2026_BASE.docx`.
- Reemplazo automático de variables principales.
- Tabla dinámica de facturas.
- Tabla alineada del detalle económico del Artículo 2°.
- Cálculo de importe en letras.
- Cálculo de UC desde la OP y parámetros actuales.
- Integración con el editor de disposición existente.

## Prueba recomendada

1. Crear expediente.
2. Cargar OP MONKE.
3. Ejecutar IA documental.
4. Completar checklist físico.
5. Validar expediente.
6. Generar borrador de disposición.
7. Verificar que el texto siga el modelo oficial y que se completen variables.
8. Exportar texto.
