# Commit 0005

## Objetivo

Incorporar el primer motor inteligente del SIGD-ST para analizar una Orden de Pago asociada a un expediente.

## Implementado

- Endpoint de análisis de OP.
- Respuesta estructurada de datos extraídos.
- Documentos comerciales detectados.
- Retenciones detectadas.
- Cálculo de UC.
- Determinación de procedimiento.
- Advertencias y faltantes.
- Registro de historial automático.
- Vista en frontend del análisis IA.

## Endpoint nuevo

POST /expedientes/{id}/analizar-op

## Modo actual

Alfa simulado/determinístico.

Todavía no lee el PDF real. Devuelve un análisis consistente para probar el flujo completo y preparar la integración posterior con extracción real de texto/OCR/IA.

## Próximo paso

Commit 0006:
- estabilización;
- pruebas;
- corrección de errores;
- mejora de instalación;
- preparación para lectura real de PDF.
